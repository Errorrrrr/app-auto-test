from __future__ import annotations

import hashlib
import json

from pydantic import ValidationError

from ..schemas import (
    FlowValidationErrorDTO,
    FlowValidationRequest,
    FlowValidationResultDTO,
    SampleFlowDTO,
)


def validate_flow_payload(request: FlowValidationRequest) -> FlowValidationResultDTO:
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


def canonical_flow_json(flow: SampleFlowDTO) -> str:
    return json.dumps(
        flow.model_dump(mode="json"),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def flow_hash(flow: SampleFlowDTO) -> str:
    return hashlib.sha256(canonical_flow_json(flow).encode("utf-8")).hexdigest()
