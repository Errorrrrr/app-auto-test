from pathlib import Path
import json

from fastapi.testclient import TestClient

from app_auto_test.config import Settings
from app_auto_test.main import create_app


def test_create_run_with_uploaded_apk_generates_blocked_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    app = create_app(
        Settings(
            data_dir=tmp_path,
            adb_path=str(tmp_path / "missing-adb"),
            maestro_bin="missing-maestro",
            allow_real_execution=False,
        )
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/runs",
        data={
            "test_name": "Smoke",
            "platform": "android",
            "device_id": "emulator-5554",
            "package_name": "com.demo.app",
            "run_mode": "execute",
        },
        files={"apk": ("app-release.apk", b"fake-apk", "application/vnd.android.package-archive")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    run = body["data"]
    assert run["status"] == "blocked"
    assert "ADB_NOT_FOUND" in run["blocked_reasons"]
    assert run["sample_flow"]["package_name"] == "com.demo.app"

    report_response = client.get(f"/api/v1/runs/{run['run_id']}/report")
    assert report_response.status_code == 200
    report = report_response.json()["data"]["report"]
    assert report["status"] == "blocked"
    assert "Run blocked" in report["result_summary"]

    export_response = client.get(f"/api/v1/runs/{run['run_id']}/report/export?format=html")
    assert export_response.status_code == 200
    assert "text/html" in export_response.headers["content-type"]

    list_response = client.get("/api/v1/runs")
    assert list_response.status_code == 200
    listed_runs = list_response.json()["data"]["items"]
    assert listed_runs[0]["run_id"] == run["run_id"]


def test_device_contract_returns_placeholder_when_adb_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    app = create_app(Settings(data_dir=tmp_path, adb_path=str(tmp_path / "missing-adb")))
    client = TestClient(app)

    response = client.get("/api/v1/devices?platform=android")

    assert response.status_code == 200
    item = response.json()["data"]["items"][0]
    assert item["id"] == "android-adb-unavailable"
    assert item["selectable"] is False
    assert item["blocked_reason"] == "ADB_NOT_FOUND"


def test_create_run_rejects_flow_yaml_injection(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            data_dir=tmp_path,
            adb_path=str(tmp_path / "missing-adb"),
            maestro_bin="missing-maestro",
            allow_real_execution=False,
        )
    )
    client = TestClient(app)
    flow = {
        "name": "malicious",
        "platform": "android",
        "package_name": "com.demo.app",
        "steps": [
            {
                "action": "tapOn",
                "target": "Login\n- back",
            }
        ],
    }

    response = client.post(
        "/api/v1/runs",
        data={
            "test_name": "Smoke",
            "platform": "android",
            "device_id": "emulator-5554",
            "package_name": "com.demo.app",
            "sample_mode": "provided",
            "flow_json": json.dumps(flow),
            "run_mode": "execute",
        },
        files={"apk": ("app-release.apk", b"fake-apk", "application/vnd.android.package-archive")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "flowJson must be a valid SampleFlowDTO JSON object"


def test_console_routes_serve_static_assets(tmp_path: Path) -> None:
    app = create_app(Settings(data_dir=tmp_path))
    client = TestClient(app)

    index_response = client.get("/")
    assert index_response.status_code == 200
    assert "App 自动化测试控制台" in index_response.text
    assert "Codex / Cursor 交互" in index_response.text

    console_response = client.get("/console")
    assert console_response.status_code == 200
    assert "创建运行" in console_response.text
    assert "iOS 签名待补齐" in console_response.text

    script_response = client.get("/static/app.js")
    assert script_response.status_code == 200
    assert "renderAgentPrompt" in script_response.text
    assert "SampleFlowDTO JSON" in script_response.text

    style_response = client.get("/static/styles.css")
    assert style_response.status_code == 200
    assert "console-grid" in style_response.text
