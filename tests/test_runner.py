import stat
from pathlib import Path

from app_auto_test.config import Settings
from app_auto_test.schemas import (
    ApkAssetDTO,
    GenerateSampleRequest,
    RunMode,
    RunStatus,
    TestRunDTO as RunDTO,
    new_id,
)
from app_auto_test.services.devices import DeviceService
from app_auto_test.services.reports import ReportService
from app_auto_test.services.runner import LocalRunner
from app_auto_test.services.samples import SampleService
from app_auto_test.storage import JsonStore


def test_runner_writes_events_and_report_when_blocked(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path,
        adb_path=str(tmp_path / "missing-adb"),
        maestro_bin="missing-maestro",
        allow_real_execution=False,
    )
    store = JsonStore(tmp_path)
    sample_service = SampleService()
    report_service = ReportService(store)
    runner = LocalRunner(
        settings=settings,
        store=store,
        device_service=DeviceService(settings),
        sample_service=sample_service,
        report_service=report_service,
    )
    apk_path = tmp_path / "app.apk"
    apk_path.write_bytes(b"apk")
    run = RunDTO(
        run_id=new_id("run"),
        test_name="Smoke",
        platform="android",
        run_mode=RunMode.execute,
        device_id="emulator-5554",
        package_name="com.demo.app",
        apk_asset=ApkAssetDTO(
            asset_id=new_id("apk"),
            file_name="app.apk",
            content_type="application/vnd.android.package-archive",
            size_bytes=3,
            sha256="abc",
            stored_path=str(apk_path),
        ),
        sample_flow=sample_service.generate(
            GenerateSampleRequest(package_name="com.demo.app")
        ),
    )
    store.save_run(run)

    updated = runner.start(run)

    assert updated.status == RunStatus.blocked
    assert (tmp_path / "runs" / run.run_id / "flow.yaml").exists()
    assert (tmp_path / "runs" / run.run_id / "report" / "report.html").exists()
    assert [artifact.name for artifact in updated.artifacts] == ["flow.yaml"]
    assert [event["event_type"] for event in store.read_events(run.run_id)] == [
        "HEALTH_CHECKED",
        "MAESTRO_FLOW_READY",
        "RUN_BLOCKED",
    ]


def test_runner_uses_resolved_path_adb_when_configured_adb_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    command_log = tmp_path / "commands.log"
    fake_adb = bin_dir / "adb"
    fake_maestro = bin_dir / "maestro"
    fake_adb.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"devices\" ]; then\n"
        "  printf 'List of devices attached\\n'\n"
        "  printf 'emulator-5554 device product:demo model:demo\\n'\n"
        "  exit 0\n"
        "fi\n"
        f"printf '%s %s\\n' \"$0\" \"$*\" >> {command_log}\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_maestro.write_text(
        "#!/bin/sh\n"
        f"printf '%s %s\\n' \"$0\" \"$*\" >> {command_log}\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_adb.chmod(fake_adb.stat().st_mode | stat.S_IXUSR)
    fake_maestro.chmod(fake_maestro.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(bin_dir))

    settings = Settings(
        data_dir=tmp_path,
        adb_path=str(tmp_path / "missing-configured-adb"),
        maestro_bin="maestro",
        allow_real_execution=True,
    )
    store = JsonStore(tmp_path)
    sample_service = SampleService()
    report_service = ReportService(store)
    device_service = DeviceService(settings)
    runner = LocalRunner(
        settings=settings,
        store=store,
        device_service=device_service,
        sample_service=sample_service,
        report_service=report_service,
    )
    apk_path = tmp_path / "app.apk"
    apk_path.write_bytes(b"apk")
    run = RunDTO(
        run_id=new_id("run"),
        test_name="Smoke",
        platform="android",
        run_mode=RunMode.execute,
        device_id="emulator-5554",
        package_name="com.demo.app",
        apk_asset=ApkAssetDTO(
            asset_id=new_id("apk"),
            file_name="app.apk",
            content_type="application/vnd.android.package-archive",
            size_bytes=3,
            sha256="abc",
            stored_path=str(apk_path),
        ),
        sample_flow=sample_service.generate(
            GenerateSampleRequest(package_name="com.demo.app")
        ),
    )
    store.save_run(run)

    capability = device_service.check_android_capability(
        device_id="emulator-5554",
        apk_path=str(apk_path),
        package_name="com.demo.app",
    )
    updated = runner.start(run)

    assert capability.ready is True
    assert device_service.resolve_adb_command() == str(fake_adb)
    assert updated.status == RunStatus.passed
    assert (tmp_path / "runs" / run.run_id / "maestro-stdout.log").exists()
    assert (tmp_path / "runs" / run.run_id / "maestro-stderr.log").exists()
    assert (tmp_path / "runs" / run.run_id / "execution.json").exists()
    assert {artifact.name for artifact in updated.artifacts} == {
        "flow.yaml",
        "maestro-stdout.log",
        "maestro-stderr.log",
        "execution.json",
    }
    assert str(fake_adb) in command_log.read_text(encoding="utf-8")
