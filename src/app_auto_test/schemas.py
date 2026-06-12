from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class Platform(str, Enum):
    android = "android"
    ios = "ios"


class DeviceKind(str, Enum):
    emulator = "emulator"
    physical = "physical"
    simulator = "simulator"
    unknown = "unknown"


class DeviceStatus(str, Enum):
    online = "online"
    offline = "offline"
    unavailable = "unavailable"


class RunStatus(str, Enum):
    created = "created"
    health_checked = "health_checked"
    queued = "queued"
    running = "running"
    passed = "passed"
    failed = "failed"
    blocked = "blocked"
    cancelled = "cancelled"


class ReportStatus(str, Enum):
    pending = "pending"
    generated = "generated"
    blocked = "blocked"
    failed = "failed"


class RunMode(str, Enum):
    health_check = "health_check"
    execute = "execute"


class AgentProvider(str, Enum):
    codex = "codex"
    cursor = "cursor"
    manual = "manual"


class FlowReviewStatus(str, Enum):
    draft = "draft"
    validated = "validated"
    confirmed = "confirmed"
    rejected = "rejected"


class FlowAction(str, Enum):
    launch_app = "launchApp"
    tap_on = "tapOn"
    input_text = "inputText"
    assert_visible = "assertVisible"
    scroll = "scroll"
    back = "back"
    wait = "wait"
    take_screenshot = "takeScreenshot"


class ApiError(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "blocker"] = "blocker"


class ApiResponse(BaseModel):
    success: bool = True
    request_id: str = Field(default_factory=lambda: new_id("req"))
    data: Any = None
    error: ApiError | None = None


class DeviceDTO(BaseModel):
    id: str
    platform: Platform
    name: str
    kind: DeviceKind
    status: DeviceStatus
    provider: str = "local"
    serial: str | None = None
    selectable: bool = False
    blocked_reason: str | None = None


class CapabilityDTO(BaseModel):
    platform: Platform
    ready: bool
    checks: dict[str, bool]
    missing_fields: list[str] = Field(default_factory=list)
    blocked_reasons: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class FlowStepDTO(BaseModel):
    action: FlowAction
    target: str | None = None
    text: str | None = None
    timeout_ms: int | None = None
    note: str | None = None

    @field_validator("target", "text")
    @classmethod
    def reject_multiline_step_text(cls, value: str | None) -> str | None:
        return _single_line(value)


class SampleFlowDTO(BaseModel):
    sample_id: str = Field(default_factory=lambda: new_id("sample"))
    name: str
    platform: Platform = Platform.android
    package_name: str
    generated_from: str = "auto"
    steps: list[FlowStepDTO]
    requires_confirmation: bool = True
    created_at: str = Field(default_factory=utc_now)

    @field_validator("package_name")
    @classmethod
    def reject_multiline_flow_text(cls, value: str) -> str:
        return _single_line(value) or ""


class FlowValidationRequest(BaseModel):
    flow_json: str | None = None
    flow: dict[str, Any] | None = None
    platform: Platform | None = None
    package_name: str | None = None

    @field_validator("flow_json")
    @classmethod
    def reject_multiline_payload_control_chars(cls, value: str | None) -> str | None:
        if value is not None and "\x00" in value:
            raise ValueError("flowJson must not contain NUL bytes.")
        return value


class FlowValidationErrorDTO(BaseModel):
    code: str
    field: str | None = None
    message: str


class FlowValidationResultDTO(BaseModel):
    valid: bool
    flow: SampleFlowDTO | None = None
    errors: list[FlowValidationErrorDTO] = Field(default_factory=list)
    action_whitelist: list[str] = Field(
        default_factory=lambda: [action.value for action in FlowAction]
    )


class GenerateSampleRequest(BaseModel):
    app_name: str = "Android App"
    package_name: str | None = None
    goal: str | None = None
    platform: Platform = Platform.android


class ApkAssetDTO(BaseModel):
    asset_id: str
    file_name: str
    content_type: str
    size_bytes: int
    sha256: str
    stored_path: str
    package_name: str | None = None
    uploaded_at: str = Field(default_factory=utc_now)


class CreateRunRequest(BaseModel):
    test_name: str = "Android local MVP run"
    platform: Platform = Platform.android
    device_id: str | None = None
    package_name: str | None = None
    sample_mode: Literal["auto", "provided"] = "auto"
    flow: SampleFlowDTO | None = None
    run_mode: RunMode = RunMode.health_check
    agent_provider: AgentProvider = AgentProvider.manual
    agent_goal: str | None = None
    flow_review_status: FlowReviewStatus = FlowReviewStatus.draft


class RunArtifactDTO(BaseModel):
    name: str
    kind: Literal["maestro_flow", "maestro_stdout", "maestro_stderr", "execution_json"]
    path: str
    media_type: str
    size_bytes: int
    created_at: str = Field(default_factory=utc_now)


class RunEventDTO(BaseModel):
    event_id: str = Field(default_factory=lambda: new_id("evt"))
    run_id: str
    sequence: int
    event_type: str
    status: RunStatus | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    occurred_at: str = Field(default_factory=utc_now)


class ReportDTO(BaseModel):
    report_id: str
    run_id: str
    status: ReportStatus
    result_summary: str
    html_path: str | None = None
    json_path: str | None = None
    export_formats: list[str] = Field(default_factory=lambda: ["html", "json"])
    next_actions: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=utc_now)


class TestRunDTO(BaseModel):
    run_id: str
    test_name: str
    platform: Platform
    status: RunStatus = RunStatus.created
    run_mode: RunMode = RunMode.health_check
    device_id: str | None = None
    package_name: str | None = None
    apk_asset: ApkAssetDTO | None = None
    sample_flow: SampleFlowDTO | None = None
    agent_provider: AgentProvider = AgentProvider.manual
    agent_goal: str | None = None
    flow_review_status: FlowReviewStatus = FlowReviewStatus.draft
    flow_validation_errors: list[str] = Field(default_factory=list)
    artifacts: list[RunArtifactDTO] = Field(default_factory=list)
    report_status: ReportStatus = ReportStatus.pending
    blocked_reasons: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    run_dir: str | None = None
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class ToolManifestDTO(BaseModel):
    allowed_tools: list[str]
    denied_tools: list[str]
    provider_boundary: str
    real_execution_enabled: bool


def path_to_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _single_line(value: str | None) -> str | None:
    if value is None:
        return None
    if any(char in value for char in ("\r", "\n", "\x00")):
        raise ValueError("Flow text fields must be single-line strings.")
    return value
