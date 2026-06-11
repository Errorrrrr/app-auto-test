from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import ApkAssetDTO, TestRunDTO, utc_now


class JsonStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.assets_dir = data_dir / "assets"
        self.runs_dir = data_dir / "runs"
        self.state_path = data_dir / "state.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"assets": {}, "runs": {}}
        with self.state_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def save_state(self, state: dict[str, Any]) -> None:
        tmp_path = self.state_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, ensure_ascii=False)
        tmp_path.replace(self.state_path)

    def save_asset(self, asset: ApkAssetDTO) -> ApkAssetDTO:
        state = self.load_state()
        state.setdefault("assets", {})[asset.asset_id] = asset.model_dump()
        self.save_state(state)
        return asset

    def get_asset(self, asset_id: str) -> ApkAssetDTO | None:
        state = self.load_state()
        raw = state.get("assets", {}).get(asset_id)
        return ApkAssetDTO(**raw) if raw else None

    def save_run(self, run: TestRunDTO) -> TestRunDTO:
        state = self.load_state()
        run.updated_at = utc_now()
        state.setdefault("runs", {})[run.run_id] = run.model_dump()
        self.save_state(state)
        return run

    def get_run(self, run_id: str) -> TestRunDTO | None:
        state = self.load_state()
        raw = state.get("runs", {}).get(run_id)
        return TestRunDTO(**raw) if raw else None

    def run_dir(self, run_id: str) -> Path:
        path = self.runs_dir / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def append_event(self, run_id: str, event: dict[str, Any]) -> None:
        run_dir = self.run_dir(run_id)
        with (run_dir / "events.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    def read_events(self, run_id: str) -> list[dict[str, Any]]:
        events_path = self.run_dir(run_id) / "events.jsonl"
        if not events_path.exists():
            return []
        with events_path.open("r", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

