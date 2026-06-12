from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from .config import Settings, get_settings
from .schemas import (
    AgentProvider,
    ApiError,
    ApiResponse,
    FlowAction,
    FlowReviewStatus,
    FlowValidationErrorDTO,
    FlowValidationRequest,
    FlowValidationResultDTO,
    GenerateSampleRequest,
    Platform,
    RunMode,
    TestRunDTO,
    ToolManifestDTO,
    new_id,
)
from .services.assets import AssetService
from .services.devices import DeviceService
from .services.reports import ReportService
from .services.runner import LocalRunner
from .services.samples import SampleService
from .storage import JsonStore


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    store = JsonStore(settings.data_dir)
    asset_service = AssetService(store)
    device_service = DeviceService(settings)
    sample_service = SampleService()
    report_service = ReportService(store)
    runner = LocalRunner(
        settings=settings,
        store=store,
        device_service=device_service,
        sample_service=sample_service,
        report_service=report_service,
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
            )
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
    ) -> ApiResponse:
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
        effective_package = package_name or asset.package_name
        flow = None
        if sample_mode == "provided" and flow_json:
            flow_validation = _validate_flow_payload(
                FlowValidationRequest(
                    flow_json=flow_json,
                    platform=platform,
                    package_name=effective_package,
                )
            )
            if not flow_validation.valid or not flow_validation.flow:
                raise HTTPException(
                    status_code=400,
                    detail="flowJson must be a valid SampleFlowDTO JSON object",
                )
            flow = flow_validation.flow
            effective_package = effective_package or flow.package_name
        else:
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
    from .schemas import SampleFlowDTO

    errors: list[FlowValidationErrorDTO] = []
    if request.flow_json is not None and request.flow is not None:
        errors.append(
            FlowValidationErrorDTO(
                code="FLOW_PAYLOAD_AMBIGUOUS",
                message="Provide either flowJson or flow, not both.",
            )
        )
        return FlowValidationResultDTO(valid=False, errors=errors)

    raw_payload = request.flow
    if request.flow_json is not None:
        try:
            raw_payload = json.loads(request.flow_json)
        except json.JSONDecodeError:
            errors.append(
                FlowValidationErrorDTO(
                    code="FLOW_JSON_INVALID",
                    field="flowJson",
                    message="flowJson must be a JSON SampleFlowDTO object, not Maestro YAML or free text.",
                )
            )
            return FlowValidationResultDTO(valid=False, errors=errors)

    if raw_payload is None:
        errors.append(
            FlowValidationErrorDTO(
                code="FLOW_PAYLOAD_MISSING",
                message="Provide a SampleFlowDTO JSON object to validate.",
            )
        )
        return FlowValidationResultDTO(valid=False, errors=errors)
    if not isinstance(raw_payload, dict):
        errors.append(
            FlowValidationErrorDTO(
                code="FLOW_PAYLOAD_NOT_OBJECT",
                message="SampleFlowDTO must be a JSON object.",
            )
        )
        return FlowValidationResultDTO(valid=False, errors=errors)

    try:
        flow = SampleFlowDTO.model_validate(raw_payload)
    except ValidationError as exc:
        return FlowValidationResultDTO(
            valid=False,
            errors=[
                FlowValidationErrorDTO(
                    code="FLOW_SCHEMA_INVALID",
                    field=".".join(str(part) for part in error["loc"]) or None,
                    message=str(error["msg"]),
                )
                for error in exc.errors()
            ],
        )

    if request.platform and flow.platform != request.platform:
        errors.append(
            FlowValidationErrorDTO(
                code="FLOW_PLATFORM_MISMATCH",
                field="platform",
                message="Flow platform must match the selected run platform.",
            )
        )
    if request.package_name and flow.package_name != request.package_name:
        errors.append(
            FlowValidationErrorDTO(
                code="FLOW_PACKAGE_NAME_MISMATCH",
                field="package_name",
                message="Flow packageName must match the uploaded app packageName.",
            )
        )
    if not flow.steps:
        errors.append(
            FlowValidationErrorDTO(
                code="FLOW_STEPS_EMPTY",
                field="steps",
                message="Flow must contain at least one controlled action.",
            )
        )

    return FlowValidationResultDTO(valid=not errors, flow=None if errors else flow, errors=errors)


app = create_app()
