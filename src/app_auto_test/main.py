from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings, get_settings
from .schemas import (
    AgentProvider,
    ApiError,
    ApiResponse,
    ConfirmTestcaseFlowDraftRequest,
    FlowAction,
    FlowReviewStatus,
    FlowValidationRequest,
    FlowValidationResultDTO,
    GenerateSampleRequest,
    Platform,
    PrivacyStatus,
    RejectTestcaseFlowDraftRequest,
    RunMode,
    TestcaseDraftStatus,
    TestRunDTO,
    ToolManifestDTO,
    new_id,
)
from .services.assets import AssetService
from .services.devices import DeviceService
from .services.flow_validation import flow_hash, validate_flow_payload
from .services.providers import LocalArtifactProvider, NoopModelAnalysisProvider
from .services.reports import ReportService
from .services.runner import LocalRunner
from .services.samples import SampleService
from .services.testcase_files import TestcaseFileError, TestcaseFileService
from .storage import JsonStore


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    store = JsonStore(settings.data_dir)
    asset_service = AssetService(store)
    testcase_file_service = TestcaseFileService(store)
    device_service = DeviceService(settings)
    sample_service = SampleService()
    report_service = ReportService(store)
    artifact_provider = LocalArtifactProvider(store)
    model_provider = NoopModelAnalysisProvider()
    runner = LocalRunner(
        settings=settings,
        store=store,
        device_service=device_service,
        sample_service=sample_service,
        report_service=report_service,
        artifact_provider=artifact_provider,
        model_provider=model_provider,
    )

    app = FastAPI(
        title="App Auto Test Backend",
        version="0.1.0",
        description="Local API and runner foundation for app automation.",
    )
    web_dir = Path(__file__).parent / "web"
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/", include_in_schema=False)
    def console_index() -> FileResponse:
        return FileResponse(web_dir / "index.html")

    @app.get("/console", include_in_schema=False)
    def console_alias() -> FileResponse:
        return FileResponse(web_dir / "index.html")

    @app.get("/api/v1/health", response_model=ApiResponse)
    def health() -> ApiResponse:
        return ApiResponse(
            data={
                "status": "ok",
                "dataDir": str(settings.data_dir),
                "realExecutionEnabled": settings.allow_real_execution,
            }
        )

    @app.get("/api/v1/tools/manifest", response_model=ApiResponse)
    def tool_manifest() -> ApiResponse:
        return ApiResponse(
            data=ToolManifestDTO(
                allowed_tools=[action.value for action in FlowAction],
                denied_tools=[
                    "shell",
                    "network_request",
                    "read_secret",
                    "write_file",
                    "raw_device_control",
                ],
                provider_boundary="Only the local runner may call adb or Maestro; generated flows require review.",
                real_execution_enabled=settings.allow_real_execution,
                provider_boundaries={
                    "execution": "ExecutionProvider is local Maestro and remains gated by APP_AUTO_TEST_ALLOW_REAL_EXECUTION.",
                    "device": "DeviceProvider only performs local readiness checks until real device inputs are supplied.",
                    "artifact": "ArtifactProvider stores files under APP_AUTO_TEST_DATA_DIR; real OSS is not configured.",
                    "model": "ModelAnalysisProvider is noop and never calls an external model.",
                },
                local_gate_commands=["scripts/local-gate.sh"],
            )
        )

    @app.get("/api/v1/providers/readiness", response_model=ApiResponse)
    def provider_readiness() -> ApiResponse:
        execution_blocked = [] if settings.allow_real_execution else ["REAL_EXECUTION_DISABLED"]
        execution_actions = (
            []
            if settings.allow_real_execution
            else ["Set APP_AUTO_TEST_ALLOW_REAL_EXECUTION=true only after runner permissions and device inputs are reviewed."]
        )
        return ApiResponse(
            data={
                "items": [
                    {
                        "name": runner.execution_provider.provider_name,
                        "kind": "execution",
                        "mode": "local",
                        "ready": settings.allow_real_execution,
                        "checks": {
                            "realExecutionEnabled": settings.allow_real_execution,
                            "androidOnly": True,
                            "iosProviderConfigured": False,
                        },
                        "blocked_reasons": execution_blocked,
                        "next_actions": execution_actions,
                        "external_calls_enabled": settings.allow_real_execution,
                    },
                    {
                        "name": device_service.provider_name,
                        "kind": "device",
                        "mode": "local",
                        "ready": False,
                        "checks": {
                            "androidPreflightAvailable": True,
                            "iosReadinessOnly": True,
                            "realDeviceAttachedByThisEndpoint": False,
                        },
                        "blocked_reasons": ["REAL_DEVICE_INPUTS_NOT_CONFIRMED"],
                        "next_actions": [
                            "Provide target devices or a cloud-device plan before real provider validation.",
                        ],
                        "external_calls_enabled": False,
                    },
                    artifact_provider.readiness(),
                    model_provider.readiness(),
                ]
            }
        )

    @app.get("/api/v1/devices", response_model=ApiResponse)
    def list_devices(platform: Platform = Query(default=Platform.android)) -> ApiResponse:
        return ApiResponse(data={"items": device_service.list_devices(platform)})

    @app.post("/api/v1/capabilities/check", response_model=ApiResponse)
    def check_capability(
        platform: Platform = Form(default=Platform.android),
        device_id: str | None = Form(default=None),
        apk_path: str | None = Form(default=None),
        package_name: str | None = Form(default=None),
    ) -> ApiResponse:
        if platform == Platform.ios:
            return ApiResponse(data=device_service.check_ios_capability())
        return ApiResponse(
            data=device_service.check_android_capability(
                device_id=device_id,
                apk_path=apk_path,
                package_name=package_name,
            )
        )

    @app.post("/api/v1/samples/generate", response_model=ApiResponse)
    def generate_sample(request: GenerateSampleRequest) -> ApiResponse:
        return ApiResponse(data=sample_service.generate(request))

    @app.post("/api/v1/flows/validate", response_model=ApiResponse)
    def validate_flow(request: FlowValidationRequest) -> ApiResponse:
        return ApiResponse(data=_validate_flow_payload(request))

    @app.post("/api/v1/testcase-files", response_model=ApiResponse)
    async def upload_testcase_file(
        file: UploadFile = File(...),
        platform: Platform = Form(default=Platform.android),
        package_name: str = Form(...),
        test_name: str | None = Form(default=None),
    ) -> ApiResponse:
        try:
            draft = await testcase_file_service.create_draft(
                upload=file,
                platform=platform,
                package_name=package_name,
                test_name=test_name,
            )
        except TestcaseFileError as exc:
            _raise_api_error(exc.code, exc.message, exc.status_code)
        return ApiResponse(data=draft)

    @app.get("/api/v1/testcase-files/{draft_id}", response_model=ApiResponse)
    def get_testcase_file_draft(draft_id: str) -> ApiResponse:
        try:
            return ApiResponse(data=testcase_file_service.get_draft(draft_id))
        except TestcaseFileError as exc:
            _raise_api_error(exc.code, exc.message, exc.status_code)

    @app.post("/api/v1/testcase-files/{draft_id}/confirm", response_model=ApiResponse)
    def confirm_testcase_file_draft(
        draft_id: str,
        request: ConfirmTestcaseFlowDraftRequest,
    ) -> ApiResponse:
        try:
            return ApiResponse(data=testcase_file_service.confirm_draft(draft_id, request))
        except TestcaseFileError as exc:
            _raise_api_error(exc.code, exc.message, exc.status_code)

    @app.post("/api/v1/testcase-files/{draft_id}/reject", response_model=ApiResponse)
    def reject_testcase_file_draft(
        draft_id: str,
        request: RejectTestcaseFlowDraftRequest | None = None,
    ) -> ApiResponse:
        _ = request
        try:
            return ApiResponse(data=testcase_file_service.reject_draft(draft_id))
        except TestcaseFileError as exc:
            _raise_api_error(exc.code, exc.message, exc.status_code)

    @app.post("/api/v1/assets/apk", response_model=ApiResponse)
    async def upload_apk(apk: UploadFile = File(...)) -> ApiResponse:
        asset = await asset_service.save_apk(apk)
        return ApiResponse(data=asset)

    @app.post("/api/v1/runs", response_model=ApiResponse)
    async def create_run(
        apk: UploadFile = File(...),
        test_name: str = Form(default="Android local MVP run"),
        platform: Platform = Form(default=Platform.android),
        device_id: str | None = Form(default=None),
        package_name: str | None = Form(default=None),
        sample_mode: str = Form(default="auto"),
        flow_json: str | None = Form(default=None),
        run_mode: RunMode = Form(default=RunMode.health_check),
        agent_provider: AgentProvider = Form(default=AgentProvider.manual),
        agent_goal: str | None = Form(default=None),
        flow_review_status: FlowReviewStatus = Form(default=FlowReviewStatus.draft),
        flow_draft_id: str | None = Form(default=None),
    ) -> ApiResponse:
        effective_package = package_name
        flow = None
        if sample_mode == "provided":
            if flow_review_status != FlowReviewStatus.confirmed:
                _raise_api_error(
                    "FLOW_CONFIRMATION_REQUIRED",
                    "sample_mode=provided requires flow_review_status=confirmed before creating a run.",
                )

            draft = None
            if flow_draft_id:
                draft = store.get_testcase_draft(flow_draft_id)
                if not draft:
                    _raise_api_error(
                        "FLOW_DRAFT_NOT_FOUND",
                        "Confirmed testcase flow draft was not found.",
                        404,
                    )
                effective_package = effective_package or draft.package_name
                if draft.privacy_status not in {PrivacyStatus.clean, PrivacyStatus.redacted}:
                    _raise_api_error(
                        "CASE_PRIVACY_BLOCKED",
                        "Privacy status blocks this testcase flow draft from creating a run.",
                    )
                if (
                    draft.status != TestcaseDraftStatus.confirmed
                    or draft.flow_review_status != FlowReviewStatus.confirmed
                ):
                    _raise_api_error(
                        "FLOW_DRAFT_NOT_CONFIRMED",
                        "Testcase flow draft must be confirmed before creating a run.",
                    )
                if not draft.validation or not draft.validation.valid or not draft.sample_flow:
                    _raise_api_error(
                        "FLOW_DRAFT_NOT_CONFIRMED",
                        "Confirmed testcase flow draft must include a valid SampleFlowDTO.",
                    )

            if flow_json:
                flow_validation = _validate_flow_payload(
                    FlowValidationRequest(
                        flow_json=flow_json,
                        platform=platform,
                        package_name=effective_package,
                    )
                )
                if not flow_validation.valid or not flow_validation.flow:
                    _raise_api_error(
                        "FLOW_JSON_INVALID",
                        "flowJson must be a valid SampleFlowDTO JSON object.",
                    )
                flow = flow_validation.flow
            elif draft and draft.sample_flow:
                flow = draft.sample_flow
            else:
                _raise_api_error(
                    "FLOW_PAYLOAD_MISSING",
                    "sample_mode=provided requires flow_json or flow_draft_id.",
                )

            effective_package = effective_package or flow.package_name
            if draft:
                if not draft.confirmed_flow_hash or flow_hash(flow) != draft.confirmed_flow_hash:
                    _raise_api_error(
                        "FLOW_DRAFT_HASH_MISMATCH",
                        "Submitted flow_json does not match the confirmed testcase flow draft.",
                    )

        if platform == Platform.ios:
            capability = device_service.check_ios_capability()
            return ApiResponse(
                success=False,
                data=capability,
                error=ApiError(
                    code="IOS_EXECUTION_BLOCKED",
                    message="iOS real execution is blocked until artifact, bundleId and signing inputs are provided.",
                ),
            )

        asset = await asset_service.save_apk(apk)
        effective_package = effective_package or asset.package_name
        if sample_mode != "provided":
            flow = sample_service.generate(
                GenerateSampleRequest(
                    app_name=test_name,
                    package_name=effective_package,
                    platform=platform,
                )
            )

        run = TestRunDTO(
            run_id=new_id("run"),
            test_name=test_name,
            platform=platform,
            run_mode=run_mode,
            device_id=device_id,
            package_name=effective_package,
            apk_asset=asset,
            sample_flow=flow,
            flow_draft_id=flow_draft_id,
            agent_provider=agent_provider,
            agent_goal=agent_goal,
            flow_review_status=flow_review_status,
        )
        store.save_run(run)
        updated = runner.start(run)
        return ApiResponse(data=updated)

    @app.get("/api/v1/runs", response_model=ApiResponse)
    def list_runs() -> ApiResponse:
        raw_runs = store.load_state().get("runs", {})
        runs = [TestRunDTO(**item) for item in raw_runs.values()]
        runs.sort(key=lambda item: item.created_at, reverse=True)
        return ApiResponse(data={"items": runs})

    @app.post("/api/v1/runs/{run_id}/start", response_model=ApiResponse)
    def start_run(run_id: str) -> ApiResponse:
        run = store.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return ApiResponse(data=runner.start(run))

    @app.get("/api/v1/runs/{run_id}", response_model=ApiResponse)
    def get_run(run_id: str) -> ApiResponse:
        run = store.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return ApiResponse(data=run)

    @app.get("/api/v1/runs/{run_id}/events", response_model=ApiResponse)
    def get_events(run_id: str) -> ApiResponse:
        if not store.get_run(run_id):
            raise HTTPException(status_code=404, detail="Run not found")
        return ApiResponse(data={"items": store.read_events(run_id)})

    @app.get("/api/v1/runs/{run_id}/artifacts", response_model=ApiResponse)
    def list_artifacts(run_id: str) -> ApiResponse:
        run = store.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return ApiResponse(data={"items": runner.refresh_artifacts(run)})

    @app.get("/api/v1/runs/{run_id}/artifacts/maestro-flow")
    def get_maestro_flow(run_id: str) -> FileResponse:
        if not store.get_run(run_id):
            raise HTTPException(status_code=404, detail="Run not found")
        path = store.run_dir(run_id) / "flow.yaml"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Maestro flow artifact not found")
        return FileResponse(
            path=path,
            media_type="text/yaml",
            filename=f"{run_id}-flow.yaml",
        )

    @app.get("/api/v1/runs/{run_id}/report", response_model=ApiResponse)
    def get_report(run_id: str) -> ApiResponse:
        if not store.get_run(run_id):
            raise HTTPException(status_code=404, detail="Run not found")
        payload = report_service.get_report_payload(run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="Report not found")
        return ApiResponse(data=payload)

    @app.get("/api/v1/runs/{run_id}/report/export")
    def export_report(run_id: str, format: str = Query(default="html")) -> FileResponse:
        if not store.get_run(run_id):
            raise HTTPException(status_code=404, detail="Run not found")
        report_path = report_service.report_file(run_id, format)
        if report_path is None:
            raise HTTPException(status_code=404, detail="Report export not found")
        media_type = "text/html" if format == "html" else "application/json"
        return FileResponse(
            path=report_path,
            media_type=media_type,
            filename=f"{run_id}-report.{format}",
        )

    return app


def _validate_flow_payload(request: FlowValidationRequest) -> FlowValidationResultDTO:
    return validate_flow_payload(request)


def _raise_api_error(code: str, message: str, status_code: int = 400) -> None:
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


app = create_app()
