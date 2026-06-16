from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ..schemas import (
    ModelAnalysisRequestDTO,
    ModelAnalysisResultDTO,
    ModelAnalysisStatus,
    ProviderReadinessDTO,
    RunArtifactDTO,
    TestRunDTO,
)
from ..storage import JsonStore


@dataclass(frozen=True)
class ArtifactSpec:
    name: str
    kind: str
    media_type: str


ARTIFACT_SPECS = {
    "flow.yaml": ArtifactSpec("flow.yaml", "maestro_flow", "text/yaml"),
    "maestro-stdout.log": ArtifactSpec("maestro-stdout.log", "maestro_stdout", "text/plain"),
    "maestro-stderr.log": ArtifactSpec("maestro-stderr.log", "maestro_stderr", "text/plain"),
    "execution.json": ArtifactSpec("execution.json", "execution_json", "application/json"),
}


class ExecutionProvider(Protocol):
    provider_name: str

    def write_flow(self, run: TestRunDTO) -> Path:
        ...

    def execute_android(self, run: TestRunDTO, adb: str) -> Any:
        ...


class ArtifactProvider(Protocol):
    provider_name: str

    def list_run_artifacts(self, run: TestRunDTO) -> list[RunArtifactDTO]:
        ...

    def readiness(self) -> ProviderReadinessDTO:
        ...


class ModelAnalysisProvider(Protocol):
    provider_name: str

    def analyze(self, request: ModelAnalysisRequestDTO) -> ModelAnalysisResultDTO:
        ...

    def readiness(self) -> ProviderReadinessDTO:
        ...


class LocalArtifactProvider:
    provider_name = "local-filesystem"

    def __init__(self, store: JsonStore, *, retention_days: int = 7):
        self.store = store
        self.retention_days = retention_days

    def list_run_artifacts(self, run: TestRunDTO) -> list[RunArtifactDTO]:
        run_dir = self.store.run_dir(run.run_id)
        artifacts: list[RunArtifactDTO] = []
        for spec in ARTIFACT_SPECS.values():
            path = run_dir / spec.name
            if not path.exists():
                continue
            artifacts.append(
                RunArtifactDTO(
                    name=spec.name,
                    kind=spec.kind,
                    path=str(path),
                    media_type=spec.media_type,
                    size_bytes=path.stat().st_size,
                    sha256=_sha256_file(path),
                    storage_provider=self.provider_name,
                    uri=f"local://runs/{run.run_id}/{spec.name}",
                    retention_days=self.retention_days,
                )
            )
        return artifacts

    def readiness(self) -> ProviderReadinessDTO:
        return ProviderReadinessDTO(
            name=self.provider_name,
            kind="artifact",
            mode="local",
            ready=True,
            checks={
                "localFilesystemWritable": True,
                "signedUrlConfigured": False,
                "ossConfigured": False,
            },
            blocked_reasons=["OSS_PROVIDER_NOT_CONFIGURED"],
            next_actions=[
                "Configure an OSS/CDN adapter, credentials, signed URL policy and retention cleanup before remote artifact storage.",
            ],
            external_calls_enabled=False,
        )


class NoopModelAnalysisProvider:
    provider_name = "noop-model"

    def analyze(self, request: ModelAnalysisRequestDTO) -> ModelAnalysisResultDTO:
        return ModelAnalysisResultDTO(
            provider=self.provider_name,
            status=ModelAnalysisStatus.skipped,
            summary="External model analysis is disabled; no model provider was called.",
            external_call_made=False,
            blocked_reasons=["MODEL_PROVIDER_NOT_CONFIGURED"],
            audit={
                "runId": request.run_id,
                "privacyStatus": request.privacy_status.value,
                "sanitizedPayloadFields": sorted(request.sanitized_payload),
                "failClosed": True,
            },
        )

    def readiness(self) -> ProviderReadinessDTO:
        return ProviderReadinessDTO(
            name=self.provider_name,
            kind="model",
            mode="noop",
            ready=True,
            checks={
                "externalModelConfigured": False,
                "externalCallMade": False,
                "failClosed": True,
            },
            blocked_reasons=["MODEL_PROVIDER_NOT_CONFIGURED"],
            next_actions=[
                "Choose an approved model provider, credentials handoff path, redaction scope and audit retention before enabling analysis.",
            ],
            external_calls_enabled=False,
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
