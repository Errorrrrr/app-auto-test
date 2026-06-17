from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..config import Settings
from ..schemas import (
    CapabilityDTO,
    ReportStatus,
    RunEventDTO,
    RunMode,
    RunStatus,
    TestRunDTO,
    utc_now,
)
from ..storage import JsonStore
from .devices import DeviceService
from .providers import (
    ArtifactProvider,
    ExecutionProvider,
    LocalArtifactProvider,
    ModelAnalysisProvider,
    NoopModelAnalysisProvider,
)
from .privacy_patterns import BLOCK_PATTERNS
from .reports import ReportService
from .samples import SampleService


MAX_COMMAND_LOG_CHARS = 20_000


@dataclass
class MaestroExecutionResult:
    passed: bool
    exit_code: int | None
    install_exit_code: int | None
    maestro_exit_code: int | None
    error: str | None
    details: dict


class MaestroRunner:
    provider_name = "local-maestro"

    def __init__(
        self,
        *,
        settings: Settings,
        store: JsonStore,
        sample_service: SampleService,
    ):
        self.settings = settings
        self.store = store
        self.sample_service = sample_service

    def write_flow(self, run: TestRunDTO) -> Path:
        if not run.sample_flow:
            raise ValueError("sample_flow is required before writing Maestro flow.")
        path = self.store.run_dir(run.run_id) / "flow.yaml"
        path.write_text(
            self.sample_service.to_maestro_yaml(run.sample_flow),
            encoding="utf-8",
        )
        return path

    def execute_android(self, run: TestRunDTO, adb: str) -> MaestroExecutionResult:
        run_dir = self.store.run_dir(run.run_id)
        stdout_path = run_dir / "maestro-stdout.log"
        stderr_path = run_dir / "maestro-stderr.log"
        execution_path = run_dir / "execution.json"
        flow_path = run_dir / "flow.yaml"
        started_at = utc_now()
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        install_exit_code: int | None = None
        maestro_exit_code: int | None = None
        exit_code: int | None = None
        error: str | None = None

        try:
            install = subprocess.run(
                [
                    adb,
                    "-s",
                    run.device_id or "",
                    "install",
                    "-r",
                    run.apk_asset.stored_path,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            install_exit_code = install.returncode
            stdout_parts.append("[adb install]\n" + (install.stdout or ""))
            stderr_parts.append("[adb install]\n" + (install.stderr or ""))
            if install.returncode != 0:
                exit_code = install.returncode
                error = "ADB_INSTALL_FAILED"
            else:
                maestro = subprocess.run(
                    [self.settings.maestro_bin, "test", str(flow_path)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                maestro_exit_code = maestro.returncode
                exit_code = maestro.returncode
                stdout_parts.append("[maestro test]\n" + (maestro.stdout or ""))
                stderr_parts.append("[maestro test]\n" + (maestro.stderr or ""))
                if maestro.returncode != 0:
                    error = "MAESTRO_TEST_FAILED"
        except subprocess.TimeoutExpired as exc:
            exit_code = None
            error = "MAESTRO_TIMEOUT"
            stdout_parts.append(_command_output_text(exc.stdout))
            stderr_parts.append(_command_output_text(exc.stderr))
            stderr_parts.append(str(exc))
        except OSError as exc:
            exit_code = None
            error = "MAESTRO_COMMAND_ERROR"
            stderr_parts.append(str(exc))

        passed = error is None and exit_code == 0
        execution = {
            "runId": run.run_id,
            "status": "passed" if passed else "failed",
            "exitCode": exit_code,
            "installExitCode": install_exit_code,
            "maestroExitCode": maestro_exit_code,
            "error": error,
            "adbCommand": adb,
            "maestroCommand": self.settings.maestro_bin,
            "flowPath": str(flow_path),
            "startedAt": started_at,
            "finishedAt": utc_now(),
        }
        stdout_path.write_text(_sanitize_command_log("\n".join(stdout_parts)), encoding="utf-8")
        stderr_path.write_text(_sanitize_command_log("\n".join(stderr_parts)), encoding="utf-8")
        execution_path.write_text(
            json.dumps(execution, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return MaestroExecutionResult(
            passed=passed,
            exit_code=exit_code,
            install_exit_code=install_exit_code,
            maestro_exit_code=maestro_exit_code,
            error=error,
            details=execution,
        )


class LocalRunner:
    def __init__(
        self,
        *,
        settings: Settings,
        store: JsonStore,
        device_service: DeviceService,
        sample_service: SampleService,
        report_service: ReportService,
        execution_provider: ExecutionProvider | None = None,
        artifact_provider: ArtifactProvider | None = None,
        model_provider: ModelAnalysisProvider | None = None,
    ):
        self.settings = settings
        self.store = store
        self.device_service = device_service
        self.sample_service = sample_service
        self.report_service = report_service
        self.execution_provider = execution_provider or MaestroRunner(
            settings=settings,
            store=store,
            sample_service=sample_service,
        )
        self.artifact_provider = artifact_provider or LocalArtifactProvider(store)
        self.model_provider = model_provider or NoopModelAnalysisProvider()

    def start(self, run: TestRunDTO) -> TestRunDTO:
        run_dir = self.store.run_dir(run.run_id)
        run.run_dir = str(run_dir)
        capability = self.device_service.check_android_capability(
            device_id=run.device_id,
            apk_path=run.apk_asset.stored_path if run.apk_asset else None,
            package_name=run.package_name,
        )
        self._event(run, "HEALTH_CHECKED", RunStatus.health_checked, "Capability check completed.", capability.model_dump())

        if run.sample_flow:
            flow_path = self.execution_provider.write_flow(run)
            self.refresh_artifacts(run)
            self._event(
                run,
                "MAESTRO_FLOW_READY",
                RunStatus.health_checked,
                "Maestro flow artifact is ready for review.",
                {"path": str(flow_path)},
            )

        if not capability.ready:
            run.status = RunStatus.blocked
            run.blocked_reasons = capability.blocked_reasons
            run.next_actions = capability.next_actions
            self._event(
                run,
                "RUN_BLOCKED",
                RunStatus.blocked,
                "Run blocked before device execution.",
                {
                    "missingFields": capability.missing_fields,
                    "nextActions": capability.next_actions,
                },
            )
            self.refresh_artifacts(run)
            report = self.report_service.generate(run)
            run.report_status = report.status
            return self.store.save_run(run)

        if run.run_mode == RunMode.health_check:
            run.status = RunStatus.blocked
            run.blocked_reasons = ["RUN_MODE_HEALTH_CHECK_ONLY"]
            run.next_actions = ["Create the run with runMode=execute after reviewing the generated flow."]
            self._event(run, "RUN_BLOCKED", RunStatus.blocked, "Health-check mode does not execute the app.")
            self.refresh_artifacts(run)
            report = self.report_service.generate(run)
            run.report_status = report.status
            return self.store.save_run(run)

        return self._execute_android(run, capability)

    def _execute_android(self, run: TestRunDTO, capability: CapabilityDTO) -> TestRunDTO:
        if not run.apk_asset or not run.package_name:
            run.status = RunStatus.blocked
            run.blocked_reasons = ["APK_OR_PACKAGE_NAME_MISSING"]
            run.next_actions = ["Upload APK and provide packageName."]
            self._event(run, "RUN_BLOCKED", RunStatus.blocked, "APK or packageName is missing.")
            self.refresh_artifacts(run)
            report = self.report_service.generate(run)
            run.report_status = report.status
            return self.store.save_run(run)

        adb = self.device_service.resolve_adb_command()
        if not adb or not run.device_id:
            run.status = RunStatus.blocked
            run.blocked_reasons = ["ADB_OR_DEVICE_NOT_RESOLVED"]
            run.next_actions = ["Select an online Android device and configure adb before execution."]
            self._event(run, "RUN_BLOCKED", RunStatus.blocked, "Resolved adb command or deviceId is missing.")
            self.refresh_artifacts(run)
            report = self.report_service.generate(run)
            run.report_status = report.status
            return self.store.save_run(run)

        run.blocked_reasons = []
        run.next_actions = []
        run.status = RunStatus.running
        self._event(
            run,
            "RUN_STARTED",
            RunStatus.running,
            "Android execution provider started.",
            {"provider": self.execution_provider.provider_name},
        )
        self._event(
            run,
            "MAESTRO_STARTED",
            RunStatus.running,
            "Maestro execution started.",
            {"flowPath": str(self.store.run_dir(run.run_id) / "flow.yaml")},
        )
        result = self.execution_provider.execute_android(run, adb)
        self.refresh_artifacts(run)
        if result.passed:
            run.status = RunStatus.passed
            self._event(
                run,
                "MAESTRO_FINISHED",
                RunStatus.passed,
                "Maestro execution finished.",
                result.details,
            )
            self._event(run, "RUN_FINISHED", RunStatus.passed, "Android local execution passed.")
        else:
            run.status = RunStatus.failed
            self._event(
                run,
                "MAESTRO_FAILED",
                RunStatus.failed,
                "Maestro execution failed.",
                result.details,
            )
            self._event(
                run,
                "RUN_FAILED",
                RunStatus.failed,
                "Android local execution failed.",
                {"error": result.error, "capability": capability.model_dump()},
            )
        report = self.report_service.generate(run)
        run.report_status = report.status if run.status != RunStatus.failed else ReportStatus.generated
        return self.store.save_run(run)

    def refresh_artifacts(self, run: TestRunDTO):
        run.artifacts = self.artifact_provider.list_run_artifacts(run)
        return run.artifacts

    def _event(
        self,
        run: TestRunDTO,
        event_type: str,
        status: RunStatus,
        message: str,
        details: dict | None = None,
    ) -> None:
        sequence = len(self.store.read_events(run.run_id)) + 1
        event = RunEventDTO(
            run_id=run.run_id,
            sequence=sequence,
            event_type=event_type,
            status=status,
            message=message,
            details=details or {},
        )
        self.store.append_event(run.run_id, event.model_dump())

def _command_output_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _sanitize_command_log(value: str) -> str:
    sanitized = _redact_sensitive_command_log(value)
    if len(sanitized) <= MAX_COMMAND_LOG_CHARS:
        return sanitized
    omitted = len(sanitized) - MAX_COMMAND_LOG_CHARS
    return sanitized[:MAX_COMMAND_LOG_CHARS] + f"\n[TRUNCATED {omitted} chars]"


def _redact_sensitive_command_log(value: str) -> str:
    sanitized = value
    for finding_type, pattern in BLOCK_PATTERNS:
        sanitized = pattern.sub(f"[REDACTED:{finding_type}]", sanitized)
    return sanitized
