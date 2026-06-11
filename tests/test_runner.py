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
    assert [event["event_type"] for event in store.read_events(run.run_id)] == [
        "HEALTH_CHECKED",
        "SAMPLE_READY",
        "RUN_BLOCKED",
    ]
