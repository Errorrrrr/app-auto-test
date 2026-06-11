import json

from ..schemas import FlowAction, FlowStepDTO, GenerateSampleRequest, SampleFlowDTO


class SampleService:
    def generate(self, request: GenerateSampleRequest) -> SampleFlowDTO:
        package_name = request.package_name or "com.example.app"
        goal = request.goal or "open the app and verify the home screen"
        steps = [
            FlowStepDTO(action=FlowAction.launch_app, target=package_name, note="Start the uploaded APK."),
            FlowStepDTO(action=FlowAction.wait, timeout_ms=3000, note="Wait for initial screen rendering."),
            FlowStepDTO(action=FlowAction.take_screenshot, target="home_loaded"),
            FlowStepDTO(action=FlowAction.assert_visible, text="Home", note=f"Auto sample goal: {goal}"),
        ]
        return SampleFlowDTO(
            name=f"{request.app_name} smoke sample",
            platform=request.platform,
            package_name=package_name,
            steps=steps,
        )

    def to_maestro_yaml(self, flow: SampleFlowDTO) -> str:
        lines = [f"appId: {_yaml_scalar(flow.package_name)}", "---"]
        for step in flow.steps:
            if step.action == FlowAction.launch_app:
                lines.append("- launchApp")
            elif step.action == FlowAction.wait:
                timeout = step.timeout_ms or 3000
                lines.append("- extendedWaitUntil:")
                lines.append("    visible: " + _yaml_scalar(".*"))
                lines.append(f"    timeout: {timeout}")
            elif step.action == FlowAction.tap_on:
                lines.append(f"- tapOn: {_yaml_scalar(step.target or step.text or '')}")
            elif step.action == FlowAction.input_text:
                lines.append(f"- inputText: {_yaml_scalar(step.text or '')}")
            elif step.action == FlowAction.assert_visible:
                lines.append(f"- assertVisible: {_yaml_scalar(step.text or step.target or '')}")
            elif step.action == FlowAction.scroll:
                lines.append("- scroll")
            elif step.action == FlowAction.back:
                lines.append("- back")
            elif step.action == FlowAction.take_screenshot:
                lines.append(f"- takeScreenshot: {_yaml_scalar(step.target or 'screenshot')}")
            else:
                raise ValueError(f"Unsupported flow action: {step.action}")
        return "\n".join(lines) + "\n"


def _yaml_scalar(value: str) -> str:
    if any(char in value for char in ("\r", "\n", "\x00")):
        raise ValueError("Maestro YAML scalar values must be single-line strings.")
    return json.dumps(value, ensure_ascii=False)
