from ..schemas import FlowStepDTO, GenerateSampleRequest, Platform, SampleFlowDTO


class SampleService:
    def generate(self, request: GenerateSampleRequest) -> SampleFlowDTO:
        package_name = request.package_name or "com.example.app"
        goal = request.goal or "open the app and verify the home screen"
        steps = [
            FlowStepDTO(action="launchApp", target=package_name, note="Start the uploaded APK."),
            FlowStepDTO(action="wait", timeout_ms=3000, note="Wait for initial screen rendering."),
            FlowStepDTO(action="takeScreenshot", target="home_loaded"),
            FlowStepDTO(action="assertVisible", text="Home", note=f"Auto sample goal: {goal}"),
        ]
        return SampleFlowDTO(
            name=f"{request.app_name} smoke sample",
            platform=request.platform,
            package_name=package_name,
            steps=steps,
        )

    def to_maestro_yaml(self, flow: SampleFlowDTO) -> str:
        lines = [f"appId: {flow.package_name}", "---"]
        for step in flow.steps:
            if step.action == "launchApp":
                lines.append("- launchApp")
            elif step.action == "wait":
                lines.append(f"- extendedWaitUntil:\n    visible: \".*\"\n    timeout: {step.timeout_ms or 3000}")
            elif step.action == "tapOn":
                lines.append(f"- tapOn: {step.target or step.text or ''}")
            elif step.action == "inputText":
                lines.append(f"- inputText: {step.text or ''}")
            elif step.action == "assertVisible":
                lines.append(f"- assertVisible: {step.text or step.target or ''}")
            elif step.action == "scroll":
                lines.append("- scroll")
            elif step.action == "back":
                lines.append("- back")
            elif step.action == "takeScreenshot":
                lines.append(f"- takeScreenshot: {step.target or 'screenshot'}")
            else:
                lines.append(f"# Unsupported step kept for review: {step.model_dump()}")
        return "\n".join(lines) + "\n"

