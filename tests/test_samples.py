from app_auto_test.schemas import GenerateSampleRequest
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

    assert "appId: com.demo.app" in yaml
    assert "- launchApp" in yaml
    assert "- takeScreenshot: home_loaded" in yaml

