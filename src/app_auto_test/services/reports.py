from __future__ import annotations

import html
import json
from pathlib import Path

from ..schemas import ReportDTO, ReportStatus, TestRunDTO, new_id, utc_now
from ..storage import JsonStore


class ReportService:
    def __init__(self, store: JsonStore):
        self.store = store

    def generate(self, run: TestRunDTO) -> ReportDTO:
        run_dir = self.store.run_dir(run.run_id)
        report_dir = run_dir / "report"
        report_dir.mkdir(parents=True, exist_ok=True)
        events = self.store.read_events(run.run_id)
        summary = self._summary(run)
        status = ReportStatus.blocked if run.blocked_reasons else ReportStatus.generated
        report = ReportDTO(
            report_id=new_id("report"),
            run_id=run.run_id,
            status=status,
            result_summary=summary,
            html_path=str(report_dir / "report.html"),
            json_path=str(report_dir / "report.json"),
            next_actions=run.next_actions,
        )
        payload = {
            "report": report.model_dump(),
            "run": run.model_dump(),
            "events": events,
            "artifacts": [artifact.model_dump() for artifact in run.artifacts],
            "generatedAt": utc_now(),
        }
        (report_dir / "report.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (report_dir / "report.html").write_text(
            self._html(payload),
            encoding="utf-8",
        )
        return report

    def get_report_payload(self, run_id: str) -> dict | None:
        report_path = self.store.run_dir(run_id) / "report" / "report.json"
        if not report_path.exists():
            return None
        return json.loads(report_path.read_text(encoding="utf-8"))

    def report_file(self, run_id: str, fmt: str) -> Path | None:
        if fmt not in {"html", "json"}:
            return None
        path = self.store.run_dir(run_id) / "report" / f"report.{fmt}"
        return path if path.exists() else None

    def _summary(self, run: TestRunDTO) -> str:
        if run.blocked_reasons:
            return "Run blocked: " + ", ".join(run.blocked_reasons)
        return f"Run {run.status.value} for {run.test_name}"

    def _html(self, payload: dict) -> str:
        run = payload["run"]
        report = payload["report"]
        events = payload["events"]
        artifacts = payload.get("artifacts", [])
        event_items = "\n".join(
            f"<li><strong>{html.escape(event['event_type'])}</strong>: {html.escape(event['message'])}</li>"
            for event in events
        )
        artifact_items = "\n".join(
            f"<li><code>{html.escape(artifact['name'])}</code> ({html.escape(artifact['kind'])})</li>"
            for artifact in artifacts
        )
        if not artifact_items:
            artifact_items = "<li>No artifacts generated.</li>"
        actions = "\n".join(
            f"<li>{html.escape(action)}</li>" for action in report.get("next_actions", [])
        )
        if not actions:
            actions = "<li>No action required.</li>"
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>App Auto Test Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2937; }}
    h1 {{ font-size: 24px; margin-bottom: 8px; }}
    h2 {{ font-size: 18px; margin-top: 24px; }}
    code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
    .status {{ display: inline-block; padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>{html.escape(run["test_name"])}</h1>
  <p class="status">Run status: <code>{html.escape(run["status"])}</code></p>
  <p>Agent provider: <code>{html.escape(run.get("agent_provider", "manual"))}</code></p>
  <p>{html.escape(report["result_summary"])}</p>
  <h2>Blocked Reasons</h2>
  <p>{html.escape(", ".join(run.get("blocked_reasons", [])) or "None")}</p>
  <h2>Artifacts</h2>
  <ul>{artifact_items}</ul>
  <h2>Next Actions</h2>
  <ul>{actions}</ul>
  <h2>Events</h2>
  <ol>{event_items}</ol>
</body>
</html>
"""
