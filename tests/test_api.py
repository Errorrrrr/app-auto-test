import json
from pathlib import Path
import zipfile
from io import BytesIO

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

    artifact_response = client.get(f"/api/v1/runs/{run['run_id']}/artifacts")
    assert artifact_response.status_code == 200
    artifact_names = [item["name"] for item in artifact_response.json()["data"]["items"]]
    assert "flow.yaml" in artifact_names

    flow_response = client.get(f"/api/v1/runs/{run['run_id']}/artifacts/maestro-flow")
    assert flow_response.status_code == 200
    assert 'appId: "com.demo.app"' in flow_response.text

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
            "flow_review_status": "confirmed",
        },
        files={"apk": ("app-release.apk", b"fake-apk", "application/vnd.android.package-archive")},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "FLOW_JSON_INVALID"


def test_create_run_uses_provided_flow_package_name(tmp_path: Path, monkeypatch) -> None:
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
    flow = {
        "name": "agent generated smoke",
        "platform": "android",
        "package_name": "com.demo.app",
        "steps": [{"action": "launchApp", "target": "com.demo.app"}],
    }

    response = client.post(
        "/api/v1/runs",
        data={
            "test_name": "Smoke",
            "platform": "android",
            "device_id": "emulator-5554",
            "sample_mode": "provided",
            "flow_json": json.dumps(flow),
            "run_mode": "execute",
            "agent_provider": "codex",
            "flow_review_status": "confirmed",
        },
        files={"apk": ("app-release.apk", b"fake-apk", "application/vnd.android.package-archive")},
    )

    assert response.status_code == 200
    run = response.json()["data"]
    assert run["package_name"] == "com.demo.app"
    assert run["agent_provider"] == "codex"
    assert run["flow_review_status"] == "confirmed"
    assert "PACKAGE_NAME_MISSING" not in run["blocked_reasons"]


def test_validate_flow_accepts_sample_flow_json(tmp_path: Path) -> None:
    app = create_app(Settings(data_dir=tmp_path))
    client = TestClient(app)
    flow = {
        "name": "agent generated smoke",
        "platform": "android",
        "package_name": "com.demo.app",
        "steps": [
            {"action": "launchApp", "target": "com.demo.app"},
            {"action": "tapOn", "target": "Login"},
        ],
    }

    response = client.post(
        "/api/v1/flows/validate",
        json={
            "flow": flow,
            "platform": "android",
            "package_name": "com.demo.app",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["valid"] is True
    assert data["flow"]["package_name"] == "com.demo.app"
    assert "tapOn" in data["action_whitelist"]


def test_validate_flow_rejects_maestro_yaml_and_unknown_action(tmp_path: Path) -> None:
    app = create_app(Settings(data_dir=tmp_path))
    client = TestClient(app)

    yaml_response = client.post(
        "/api/v1/flows/validate",
        json={"flow_json": 'appId: "com.demo.app"\n---\n- launchApp\n'},
    )
    assert yaml_response.status_code == 200
    yaml_result = yaml_response.json()["data"]
    assert yaml_result["valid"] is False
    assert yaml_result["errors"][0]["code"] == "FLOW_JSON_INVALID"

    action_response = client.post(
        "/api/v1/flows/validate",
        json={
            "flow": {
                "name": "bad action",
                "platform": "android",
                "package_name": "com.demo.app",
                "steps": [{"action": "shell", "target": "id"}],
            }
        },
    )
    assert action_response.status_code == 200
    action_result = action_response.json()["data"]
    assert action_result["valid"] is False
    assert action_result["errors"][0]["code"] == "FLOW_SCHEMA_INVALID"
    assert action_result["errors"][0]["field"] == "steps.0.action"


def test_validate_flow_rejects_naked_sample_flow_body(tmp_path: Path) -> None:
    app = create_app(Settings(data_dir=tmp_path))
    client = TestClient(app)

    response = client.post(
        "/api/v1/flows/validate",
        json={
            "name": "naked",
            "platform": "android",
            "package_name": "com.demo.app",
            "steps": [{"action": "launchApp", "target": "com.demo.app"}],
        },
    )

    assert response.status_code == 200
    result = response.json()["data"]
    assert result["valid"] is False
    assert result["errors"][0]["code"] == "FLOW_PAYLOAD_MISSING"


def test_upload_testcase_text_creates_validated_draft_and_confirmed_run(tmp_path: Path, monkeypatch) -> None:
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

    upload_response = client.post(
        "/api/v1/testcase-files",
        data={
            "platform": "android",
            "package_name": "com.demo.app",
            "test_name": "Uploaded smoke",
        },
        files={
            "file": (
                "case.md",
                b"- tap Login\n- input alice\n- assert Welcome\n",
                "text/markdown",
            )
        },
    )
    assert upload_response.status_code == 200
    draft = upload_response.json()["data"]
    assert draft["status"] == "validated"
    assert draft["privacy_status"] == "clean"
    assert draft["flow_review_status"] == "validated"
    assert draft["sample_flow"]["generated_from"] == "testcase_upload"

    confirm_response = client.post(
        f"/api/v1/testcase-files/{draft['draft_id']}/confirm",
        json={"flow": draft["sample_flow"]},
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()["data"]
    assert confirmed["status"] == "confirmed"
    assert confirmed["flow_review_status"] == "confirmed"
    assert confirmed["confirmed_flow_hash"]

    run_response = client.post(
        "/api/v1/runs",
        data={
            "test_name": "Uploaded smoke",
            "platform": "android",
            "device_id": "emulator-5554",
            "sample_mode": "provided",
            "flow_json": json.dumps(confirmed["sample_flow"]),
            "flow_draft_id": confirmed["draft_id"],
            "flow_review_status": "confirmed",
            "run_mode": "execute",
        },
        files={"apk": ("app-release.apk", b"fake-apk", "application/vnd.android.package-archive")},
    )

    assert run_response.status_code == 200
    run = run_response.json()["data"]
    assert run["flow_draft_id"] == confirmed["draft_id"]
    assert run["sample_flow"]["name"] == "Uploaded smoke"
    assert run["status"] == "blocked"


def test_upload_testcase_docx_creates_draft(tmp_path: Path) -> None:
    app = create_app(Settings(data_dir=tmp_path))
    client = TestClient(app)

    response = client.post(
        "/api/v1/testcase-files",
        data={"platform": "android", "package_name": "com.demo.app"},
        files={
            "file": (
                "case.docx",
                _docx_bytes(["点击 登录", "看到 首页"]),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    draft = response.json()["data"]
    assert draft["status"] == "validated"
    assert [step["action"] for step in draft["sample_flow"]["steps"]] == [
        "launchApp",
        "tapOn",
        "assertVisible",
    ]


def test_upload_testcase_rejects_yaml_and_legacy_doc(tmp_path: Path) -> None:
    app = create_app(Settings(data_dir=tmp_path))
    client = TestClient(app)

    yaml_response = client.post(
        "/api/v1/testcase-files",
        data={"platform": "android", "package_name": "com.demo.app"},
        files={"file": ("flow.yaml", b'appId: "com.demo.app"\n---\n- launchApp\n', "text/yaml")},
    )
    doc_response = client.post(
        "/api/v1/testcase-files",
        data={"platform": "android", "package_name": "com.demo.app"},
        files={"file": ("legacy.doc", b"legacy", "application/msword")},
    )

    assert yaml_response.status_code == 400
    _assert_error_detail(
        yaml_response,
        "CASE_FILE_YAML_UNSUPPORTED",
        "YAML testcase uploads are not accepted; upload txt, md or docx testcase documents.",
    )
    assert doc_response.status_code == 400
    _assert_error_detail(
        doc_response,
        "CASE_FILE_LEGACY_DOC_UNSUPPORTED",
        "Legacy .doc files are not supported; save the testcase as .docx, .txt or .md.",
    )
    assert client.get("/api/v1/runs").json()["data"]["items"] == []


def test_upload_testcase_privacy_redacts_pii_and_blocks_secret(tmp_path: Path) -> None:
    app = create_app(Settings(data_dir=tmp_path))
    client = TestClient(app)

    pii_response = client.post(
        "/api/v1/testcase-files",
        data={"platform": "android", "package_name": "com.demo.app"},
        files={"file": ("case.txt", "输入 alice@example.com\n看到 首页".encode(), "text/plain")},
    )
    assert pii_response.status_code == 200
    pii_draft = pii_response.json()["data"]
    assert pii_draft["privacy_status"] == "redacted"
    assert "alice@example.com" not in pii_draft["redacted_preview"]
    assert "alice@example.com" not in json.dumps(pii_draft, ensure_ascii=False)
    assert pii_draft["privacy_findings"] == [
        {
            "type": "email",
            "severity": "warning",
            "action": "redacted",
            "count": 1,
            "fields": ["source"],
        }
    ]
    assert "kind" not in pii_draft["privacy_findings"][0]

    secret_response = client.post(
        "/api/v1/testcase-files",
        data={"platform": "android", "package_name": "com.demo.app"},
        files={"file": ("case.txt", b"token=abcdef1234567890\n- tap Login", "text/plain")},
    )
    assert secret_response.status_code == 200
    secret_draft = secret_response.json()["data"]
    assert secret_draft["status"] == "privacy_blocked"
    assert secret_draft["privacy_status"] == "blocked"
    assert "abcdef1234567890" not in secret_draft["redacted_preview"]
    assert "abcdef1234567890" not in json.dumps(secret_draft, ensure_ascii=False)

    confirm_response = client.post(
        f"/api/v1/testcase-files/{secret_draft['draft_id']}/confirm",
        json={},
    )
    assert confirm_response.status_code == 400
    _assert_error_detail(
        confirm_response,
        "CASE_PRIVACY_BLOCKED",
        "Privacy findings block this testcase flow draft.",
    )


def test_runs_gate_rejects_unconfirmed_privacy_blocked_and_hash_mismatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
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

    upload_response = client.post(
        "/api/v1/testcase-files",
        data={"platform": "android", "package_name": "com.demo.app"},
        files={"file": ("case.txt", b"tap Login\nassert Home", "text/plain")},
    )
    draft = upload_response.json()["data"]

    unconfirmed_response = client.post(
        "/api/v1/runs",
        data={
            "platform": "android",
            "sample_mode": "provided",
            "flow_json": json.dumps(draft["sample_flow"]),
            "flow_draft_id": draft["draft_id"],
            "flow_review_status": "confirmed",
        },
        files={"apk": ("app-release.apk", b"fake-apk", "application/vnd.android.package-archive")},
    )
    assert unconfirmed_response.status_code == 400
    assert unconfirmed_response.json()["detail"]["code"] == "FLOW_DRAFT_NOT_CONFIRMED"

    blocked_response = client.post(
        "/api/v1/testcase-files",
        data={"platform": "android", "package_name": "com.demo.app"},
        files={"file": ("case.txt", b"password=abcdef1234\nassert Home", "text/plain")},
    )
    blocked_draft = blocked_response.json()["data"]
    privacy_run_response = client.post(
        "/api/v1/runs",
        data={
            "platform": "android",
            "sample_mode": "provided",
            "flow_draft_id": blocked_draft["draft_id"],
            "flow_review_status": "confirmed",
        },
        files={"apk": ("app-release.apk", b"fake-apk", "application/vnd.android.package-archive")},
    )
    assert privacy_run_response.status_code == 400
    assert privacy_run_response.json()["detail"]["code"] == "CASE_PRIVACY_BLOCKED"

    confirm_response = client.post(
        f"/api/v1/testcase-files/{draft['draft_id']}/confirm",
        json={"flow": draft["sample_flow"]},
    )
    confirmed = confirm_response.json()["data"]
    changed_flow = dict(confirmed["sample_flow"])
    changed_flow["name"] = "Changed after confirm"
    mismatch_response = client.post(
        "/api/v1/runs",
        data={
            "platform": "android",
            "sample_mode": "provided",
            "flow_json": json.dumps(changed_flow),
            "flow_draft_id": confirmed["draft_id"],
            "flow_review_status": "confirmed",
        },
        files={"apk": ("app-release.apk", b"fake-apk", "application/vnd.android.package-archive")},
    )
    assert mismatch_response.status_code == 400
    assert mismatch_response.json()["detail"]["code"] == "FLOW_DRAFT_HASH_MISMATCH"
    assert client.get("/api/v1/runs").json()["data"]["items"] == []


def _assert_error_detail(response, expected_code: str, expected_message: str) -> None:
    body = response.json()
    assert sorted(body) == ["detail"]
    assert body["detail"] == {
        "code": expected_code,
        "message": expected_message,
    }


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


def _docx_bytes(paragraphs: list[str]) -> bytes:
    buffer = BytesIO()
    document_body = "".join(
        f"<w:p><w:r><w:t>{paragraph}</w:t></w:r></w:p>" for paragraph in paragraphs
    )
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        archive.writestr(
            "word/document.xml",
            (
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f"<w:body>{document_body}</w:body>"
                "</w:document>"
            ),
        )
    return buffer.getvalue()
