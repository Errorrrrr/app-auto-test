import pytest
from pydantic import ValidationError

from app_auto_test.schemas import FlowStepDTO, GenerateSampleRequest, SampleFlowDTO
from app_auto_test.services.samples import SampleService


def test_generate_sample_flow_uses_package_name() -> None:
    flow = SampleService().generate(
        GenerateSampleRequest(
            app_name="Demo",
            package_name="com.demo.app",
            goal="verify login",
        )
    )

    assert flow.package_name == "com.demo.app"
    assert flow.requires_confirmation is True
    assert [step.action for step in flow.steps] == [
        "launchApp",
        "wait",
        "takeScreenshot",
        "assertVisible",
    ]


def test_sample_flow_can_compile_to_maestro_yaml() -> None:
    service = SampleService()
    flow = service.generate(GenerateSampleRequest(package_name="com.demo.app"))

    yaml = service.to_maestro_yaml(flow)

    assert 'appId: "com.demo.app"' in yaml
    assert "- launchApp" in yaml
    assert '- takeScreenshot: "home_loaded"' in yaml


def test_sample_flow_rejects_yaml_injection_text() -> None:
    with pytest.raises(ValidationError):
        FlowStepDTO(action="tapOn", target="Login\n- back")


def test_sample_flow_rejects_unknown_action() -> None:
    with pytest.raises(ValidationError):
        FlowStepDTO(action="shell", target="id")


def test_sample_flow_quotes_safe_scalar_values() -> None:
    flow = SampleFlowDTO(
        name="Quoted",
        package_name="com.demo.app",
        steps=[
            FlowStepDTO(action="tapOn", target='Login: "primary"'),
            FlowStepDTO(action="inputText", text="alice@example.com"),
        ],
    )

    yaml = SampleService().to_maestro_yaml(flow)

    assert '- tapOn: "Login: \\"primary\\""' in yaml
    assert '- inputText: "alice@example.com"' in yaml
