from __future__ import annotations

import subprocess

from ..config import Settings
from ..schemas import (
    CapabilityDTO,
    ReportStatus,
    RunEventDTO,
    RunMode,
    RunStatus,
    TestRunDTO,
)
from ..storage import JsonStore
from .devices import DeviceService
from .reports import ReportService
from .samples import SampleService


class LocalRunner:
    def __init__(
        self,
        *,
        settings: Settings,
        store: JsonStore,
        device_service: DeviceService,
        sample_service: SampleService,
        report_service: ReportService,
    ):
        self.settings = settings
        self.store = store
        self.device_service = device_service
        self.sample_service = sample_service
        self.report_service = report_service

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
            (run_dir / "flow.yaml").write_text(
                self.sample_service.to_maestro_yaml(run.sample_flow),
                encoding="utf-8",
            )
            self._event(run, "SAMPLE_READY", RunStatus.health_checked, "Auto sample flow is ready for review.")

        if not capability.ready:
            run.status = RunStatus.blocked
            run.blocked_reasons = capability.blocked_reasons
            run.next_actions = capability.next_actions
            self._event(
                run,
                "RUN_BLOCKED",
                RunStatus.blocked,
                "Run blocked before device execution.",
                {"missingFields": capability.missing_fields, "nextActions": capability.next_actions},
            )
            report = self.report_service.generate(run)
            run.report_status = report.status
            return self.store.save_run(run)

        if run.run_mode == RunMode.health_check:
            run.status = RunStatus.blocked
            run.blocked_reasons = ["RUN_MODE_HEALTH_CHECK_ONLY"]
            run.next_actions = ["Create the run with runMode=execute after reviewing the generated flow."]
            self._event(run, "RUN_BLOCKED", RunStatus.blocked, "Health-check mode does not execute the app.")
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
            report = self.report_service.generate(run)
            run.report_status = report.status
            return self.store.save_run(run)

        run.status = RunStatus.running
        self._event(run, "RUN_STARTED", RunStatus.running, "Android local execution started.")
        try:
            subprocess.run(
                [self.settings.adb_path, "-s", run.device_id or "", "install", "-r", run.apk_asset.stored_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            subprocess.run(
                [self.settings.maestro_bin, "test", str(self.store.run_dir(run.run_id) / "flow.yaml")],
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
            run.status = RunStatus.passed
            self._event(run, "RUN_FINISHED", RunStatus.passed, "Android local execution passed.")
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            run.status = RunStatus.failed
            self._event(
                run,
                "RUN_FAILED",
                RunStatus.failed,
                "Android local execution failed.",
                {"error": str(exc), "capability": capability.model_dump()},
            )
        report = self.report_service.generate(run)
        run.report_status = report.status if run.status != RunStatus.failed else ReportStatus.generated
        return self.store.save_run(run)

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

