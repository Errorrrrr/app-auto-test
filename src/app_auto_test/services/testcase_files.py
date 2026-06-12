from __future__ import annotations

from io import BytesIO
import hashlib
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from fastapi import UploadFile

from ..schemas import (
    ConfirmTestcaseFlowDraftRequest,
    FlowAction,
    FlowReviewStatus,
    FlowStepDTO,
    FlowValidationRequest,
    Platform,
    PrivacyFindingDTO,
    PrivacyStatus,
    SampleFlowDTO,
    TestcaseDraftStatus,
    TestcaseFileAssetDTO,
    TestcaseFlowDraftDTO,
    new_id,
)
from ..storage import JsonStore
from .flow_validation import flow_hash, validate_flow_payload


MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 100_000
TEXT_EXTENSIONS = {".txt", ".text", ".md", ".markdown"}
DOCX_EXTENSIONS = {".docx"}
LEGACY_DOC_EXTENSIONS = {".doc"}
YAML_EXTENSIONS = {".yaml", ".yml"}

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class TestcaseFileError(Exception):
    def __init__(self, code: str, message: str, *, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class PrivacyScanResult:
    def __init__(
        self,
        *,
        status: PrivacyStatus,
        findings: list[PrivacyFindingDTO],
        redacted_texts: dict[str, str],
    ):
        self.status = status
        self.findings = findings
        self.redacted_texts = redacted_texts


class TestcaseFileService:
    def __init__(self, store: JsonStore):
        self.store = store

    async def create_draft(
        self,
        *,
        upload: UploadFile,
        platform: Platform,
        package_name: str,
        test_name: str | None,
    ) -> TestcaseFlowDraftDTO:
        safe_name = Path(upload.filename or "testcase.txt").name
        extension = Path(safe_name).suffix.lower()
        _reject_unsupported_extension(extension)
        raw = await upload.read()
        if len(raw) > MAX_FILE_BYTES:
            raise TestcaseFileError(
                "CASE_FILE_TOO_LARGE",
                "Testcase file must be 5MB or smaller.",
            )

        extracted_text = _extract_text(raw, extension)
        if _looks_like_maestro_yaml(extracted_text):
            raise TestcaseFileError(
                "CASE_FILE_YAML_UNSUPPORTED",
                "Upload a testcase document, not raw Maestro YAML.",
            )

        privacy = scan_texts({"source": extracted_text})
        asset = self._save_asset(
            raw=raw,
            safe_name=safe_name,
            content_type=upload.content_type or _content_type_for(extension),
        )

        base_draft = TestcaseFlowDraftDTO(
            draft_id=new_id("draft"),
            asset=asset,
            platform=platform,
            package_name=package_name,
            test_name=test_name,
            status=TestcaseDraftStatus.privacy_blocked
            if privacy.status == PrivacyStatus.blocked
            else TestcaseDraftStatus.parsed,
            privacy_status=privacy.status,
            flow_review_status=FlowReviewStatus.draft,
            redacted_preview=privacy.redacted_texts["source"],
            privacy_findings=privacy.findings,
        )
        if privacy.status == PrivacyStatus.blocked:
            return self.store.save_testcase_draft(base_draft)

        flow, warnings, unmapped = _parse_sample_flow(
            text=privacy.redacted_texts["source"],
            platform=platform,
            package_name=package_name,
            test_name=test_name,
        )
        validation = validate_flow_payload(
            FlowValidationRequest(
                flow=flow.model_dump(mode="json"),
                platform=platform,
                package_name=package_name,
            )
        )
        base_draft.sample_flow = flow
        base_draft.validation = validation
        base_draft.warnings = warnings
        base_draft.unmapped_fragments = unmapped
        if validation.valid:
            base_draft.status = TestcaseDraftStatus.validated
            base_draft.flow_review_status = FlowReviewStatus.validated
        else:
            base_draft.status = TestcaseDraftStatus.validation_failed
        return self.store.save_testcase_draft(base_draft)

    def get_draft(self, draft_id: str) -> TestcaseFlowDraftDTO:
        draft = self.store.get_testcase_draft(draft_id)
        if not draft:
            raise TestcaseFileError(
                "CASE_DRAFT_NOT_FOUND",
                "Testcase flow draft not found.",
                status_code=404,
            )
        return draft

    def confirm_draft(
        self,
        draft_id: str,
        request: ConfirmTestcaseFlowDraftRequest,
    ) -> TestcaseFlowDraftDTO:
        draft = self.get_draft(draft_id)
        if draft.status == TestcaseDraftStatus.rejected:
            raise TestcaseFileError(
                "CASE_DRAFT_REJECTED",
                "Rejected testcase flow drafts cannot be confirmed.",
            )
        if draft.privacy_status == PrivacyStatus.blocked:
            raise TestcaseFileError(
                "CASE_PRIVACY_BLOCKED",
                "Privacy findings block this testcase flow draft.",
            )
        if draft.privacy_status == PrivacyStatus.failed:
            raise TestcaseFileError(
                "CASE_PRIVACY_SCAN_FAILED",
                "Privacy scan failed closed for this testcase flow draft.",
            )

        payload_request = FlowValidationRequest(
            flow_json=request.flow_json,
            flow=request.flow if request.flow is not None else None,
            platform=draft.platform,
            package_name=draft.package_name,
        )
        if payload_request.flow is None and payload_request.flow_json is None:
            if not draft.sample_flow:
                raise TestcaseFileError("CASE_DRAFT_VALIDATION_FAILED", "Draft has no SampleFlowDTO to confirm.")
            payload_request.flow = draft.sample_flow.model_dump(mode="json")

        validation = validate_flow_payload(payload_request)
        if not validation.valid or not validation.flow:
            draft.validation = validation
            draft.status = TestcaseDraftStatus.validation_failed
            draft.flow_review_status = FlowReviewStatus.draft
            self.store.save_testcase_draft(draft)
            raise TestcaseFileError(
                "CASE_DRAFT_VALIDATION_FAILED",
                "SampleFlowDTO draft validation failed.",
            )

        privacy = scan_flow(validation.flow)
        draft.privacy_findings = privacy.findings
        draft.privacy_status = privacy.status
        if privacy.status == PrivacyStatus.blocked:
            draft.status = TestcaseDraftStatus.privacy_blocked
            draft.flow_review_status = FlowReviewStatus.draft
            draft.validation = validation
            self.store.save_testcase_draft(draft)
            raise TestcaseFileError(
                "CASE_PRIVACY_BLOCKED",
                "Privacy findings block this testcase flow draft.",
            )
        if privacy.status == PrivacyStatus.failed:
            draft.status = TestcaseDraftStatus.privacy_failed
            draft.flow_review_status = FlowReviewStatus.draft
            draft.validation = validation
            self.store.save_testcase_draft(draft)
            raise TestcaseFileError(
                "CASE_PRIVACY_SCAN_FAILED",
                "Privacy scan failed closed for this testcase flow draft.",
            )

        redacted_flow = redact_flow(validation.flow, privacy.redacted_texts)
        final_validation = validate_flow_payload(
            FlowValidationRequest(
                flow=redacted_flow.model_dump(mode="json"),
                platform=draft.platform,
                package_name=draft.package_name,
            )
        )
        if not final_validation.valid or not final_validation.flow:
            draft.validation = final_validation
            draft.status = TestcaseDraftStatus.validation_failed
            draft.flow_review_status = FlowReviewStatus.draft
            self.store.save_testcase_draft(draft)
            raise TestcaseFileError(
                "CASE_DRAFT_VALIDATION_FAILED",
                "Redacted SampleFlowDTO draft validation failed.",
            )

        draft.sample_flow = final_validation.flow
        draft.validation = final_validation
        draft.status = TestcaseDraftStatus.confirmed
        draft.flow_review_status = FlowReviewStatus.confirmed
        draft.confirmed_flow_hash = flow_hash(final_validation.flow)
        return self.store.save_testcase_draft(draft)

    def reject_draft(self, draft_id: str) -> TestcaseFlowDraftDTO:
        draft = self.get_draft(draft_id)
        draft.status = TestcaseDraftStatus.rejected
        draft.flow_review_status = FlowReviewStatus.rejected
        return self.store.save_testcase_draft(draft)

    def _save_asset(
        self,
        *,
        raw: bytes,
        safe_name: str,
        content_type: str,
    ) -> TestcaseFileAssetDTO:
        asset_id = new_id("casefile")
        asset_dir = self.store.testcase_assets_dir / asset_id
        asset_dir.mkdir(parents=True, exist_ok=True)
        destination = asset_dir / safe_name
        destination.write_bytes(raw)
        asset = TestcaseFileAssetDTO(
            asset_id=asset_id,
            file_name=safe_name,
            content_type=content_type,
            size_bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
            stored_path=str(destination),
        )
        return self.store.save_testcase_asset(asset)


def scan_flow(flow: SampleFlowDTO) -> PrivacyScanResult:
    texts: dict[str, str] = {
        "flow.name": flow.name,
        "flow.package_name": flow.package_name,
    }
    for index, step in enumerate(flow.steps):
        if step.target:
            texts[f"flow.steps.{index}.target"] = step.target
        if step.text:
            texts[f"flow.steps.{index}.text"] = step.text
        if step.note:
            texts[f"flow.steps.{index}.note"] = step.note
    return scan_texts(texts)


def redact_flow(flow: SampleFlowDTO, redacted_texts: dict[str, str]) -> SampleFlowDTO:
    raw = flow.model_dump(mode="json")
    raw["name"] = redacted_texts.get("flow.name", raw["name"])
    raw["package_name"] = redacted_texts.get("flow.package_name", raw["package_name"])
    for index, step in enumerate(raw["steps"]):
        for field in ("target", "text", "note"):
            key = f"flow.steps.{index}.{field}"
            if step.get(field) is not None and key in redacted_texts:
                step[field] = redacted_texts[key]
    return SampleFlowDTO.model_validate(raw)


def scan_texts(texts: dict[str, str]) -> PrivacyScanResult:
    try:
        findings_by_type: dict[tuple[str, str], dict[str, object]] = {}
        redacted_texts: dict[str, str] = {}
        blocked = False
        redacted = False

        for field, text in texts.items():
            redacted_value = text
            for finding_type, pattern in BLOCK_PATTERNS:
                matches = list(pattern.finditer(redacted_value))
                if not matches:
                    continue
                blocked = True
                redacted = True
                redacted_value = pattern.sub(f"[BLOCKED:{finding_type}]", redacted_value)
                _add_finding(findings_by_type, finding_type, "blocker", "blocked", len(matches), field)

            for finding_type, pattern in REDACT_PATTERNS:
                matches = list(pattern.finditer(redacted_value))
                if not matches:
                    continue
                redacted = True
                redacted_value = pattern.sub(f"[REDACTED:{finding_type}]", redacted_value)
                _add_finding(findings_by_type, finding_type, "warning", "redacted", len(matches), field)
            redacted_texts[field] = redacted_value

        findings = [
            PrivacyFindingDTO(
                type=finding_type,
                severity=str(item["severity"]),
                action=str(item["action"]),
                count=int(item["count"]),
                fields=sorted(item["fields"]),
            )
            for (finding_type, _action), item in findings_by_type.items()
        ]
        if blocked:
            status = PrivacyStatus.blocked
        elif redacted:
            status = PrivacyStatus.redacted
        else:
            status = PrivacyStatus.clean
        return PrivacyScanResult(status=status, findings=findings, redacted_texts=redacted_texts)
    except Exception:
        return PrivacyScanResult(
            status=PrivacyStatus.failed,
            findings=[
                PrivacyFindingDTO(
                    type="privacy_scan_error",
                    severity="blocker",
                    action="blocked",
                    count=1,
                    fields=sorted(texts),
                )
            ],
            redacted_texts={key: "" for key in texts},
        )


def _add_finding(
    findings: dict[tuple[str, str], dict[str, object]],
    finding_type: str,
    severity: str,
    action: str,
    count: int,
    field: str,
) -> None:
    key = (finding_type, action)
    item = findings.setdefault(
        key,
        {"severity": severity, "action": action, "count": 0, "fields": set()},
    )
    item["count"] = int(item["count"]) + count
    item["fields"].add(field)


def _reject_unsupported_extension(extension: str) -> None:
    if extension in YAML_EXTENSIONS:
        raise TestcaseFileError(
            "CASE_FILE_YAML_UNSUPPORTED",
            "YAML testcase uploads are not accepted; upload txt, md or docx testcase documents.",
        )
    if extension in LEGACY_DOC_EXTENSIONS:
        raise TestcaseFileError(
            "CASE_FILE_LEGACY_DOC_UNSUPPORTED",
            "Legacy .doc files are not supported; save the testcase as .docx, .txt or .md.",
        )
    if extension not in TEXT_EXTENSIONS | DOCX_EXTENSIONS:
        raise TestcaseFileError(
            "CASE_FILE_UNSUPPORTED_TYPE",
            "Unsupported testcase file type. Supported types: txt, md, docx.",
        )


def _extract_text(raw: bytes, extension: str) -> str:
    if not raw:
        raise TestcaseFileError("CASE_FILE_EMPTY", "Testcase file is empty.")
    if extension in TEXT_EXTENSIONS:
        text = _decode_text(raw)
    else:
        text = _extract_docx_text(raw)
    text = text.strip()
    if not text:
        raise TestcaseFileError("CASE_FILE_EMPTY", "No readable testcase text was found.")
    if len(text) > MAX_TEXT_CHARS:
        raise TestcaseFileError(
            "CASE_TEXT_TOO_LARGE",
            "Extracted testcase text must be 100000 characters or fewer.",
        )
    return text


def _decode_text(raw: bytes) -> str:
    if b"\x00" in raw:
        raise TestcaseFileError("CASE_FILE_DECODE_FAILED", "Testcase text appears to be binary.")
    for encoding in ("utf-8", "gb18030"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise TestcaseFileError("CASE_FILE_DECODE_FAILED", "Testcase text must be UTF-8 or GB18030.")
    control_chars = [char for char in text if ord(char) < 32 and char not in "\t\r\n"]
    if control_chars:
        raise TestcaseFileError("CASE_FILE_DECODE_FAILED", "Testcase text contains unsupported control characters.")
    return text


def _extract_docx_text(raw: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            names = set(archive.namelist())
            if "EncryptedPackage" in names:
                raise TestcaseFileError("CASE_FILE_DOCX_ENCRYPTED", "Encrypted docx files are not supported.")
            settings_xml = archive.read("word/settings.xml") if "word/settings.xml" in names else b""
            if b"documentProtection" in settings_xml:
                raise TestcaseFileError("CASE_FILE_DOCX_ENCRYPTED", "Protected docx files are not supported.")
            if "word/document.xml" not in names:
                raise TestcaseFileError("CASE_FILE_EMPTY", "No docx document body was found.")
            document_xml = archive.read("word/document.xml")
    except TestcaseFileError:
        raise
    except zipfile.BadZipFile as exc:
        raise TestcaseFileError("CASE_FILE_DOCX_ENCRYPTED", "Docx file could not be opened.") from exc
    except KeyError as exc:
        raise TestcaseFileError("CASE_FILE_EMPTY", "No docx document body was found.") from exc

    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError as exc:
        raise TestcaseFileError("CASE_FILE_DOCX_ENCRYPTED", "Docx document body could not be parsed.") from exc

    lines: list[str] = []
    for paragraph in root.iter(f"{W_NS}p"):
        parts = [node.text or "" for node in paragraph.iter(f"{W_NS}t")]
        line = "".join(parts).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _looks_like_maestro_yaml(text: str) -> bool:
    return bool(
        re.search(r"(?im)^\s*appId\s*:", text)
        and re.search(
            r"(?im)^\s*-\s*(launchApp|tapOn|inputText|assertVisible|scroll|back|takeScreenshot|extendedWaitUntil)\b",
            text,
        )
    )


def _parse_sample_flow(
    *,
    text: str,
    platform: Platform,
    package_name: str,
    test_name: str | None,
) -> tuple[SampleFlowDTO, list[str], list[str]]:
    steps: list[FlowStepDTO] = [
        FlowStepDTO(action=FlowAction.launch_app, target=package_name, note="Start the uploaded app."),
    ]
    warnings: list[str] = []
    unmapped: list[str] = []
    for line in _case_lines(text):
        lowered = line.lower()
        if _matches_any(lowered, ("启动", "打开app", "launch app", "open app")):
            continue
        if _matches_any(lowered, ("点击", "tap", "click")):
            steps.append(FlowStepDTO(action=FlowAction.tap_on, target=_extract_argument(line)))
        elif _matches_any(lowered, ("输入", "input", "type")):
            steps.append(FlowStepDTO(action=FlowAction.input_text, text=_extract_argument(line)))
        elif _matches_any(lowered, ("看到", "显示", "断言", "检查", "assert", "verify", "expect")):
            steps.append(FlowStepDTO(action=FlowAction.assert_visible, text=_extract_argument(line)))
        elif _matches_any(lowered, ("截图", "screenshot")):
            steps.append(FlowStepDTO(action=FlowAction.take_screenshot, target="case_step"))
        elif _matches_any(lowered, ("等待", "wait")):
            steps.append(FlowStepDTO(action=FlowAction.wait, timeout_ms=_extract_wait_ms(line)))
        elif _matches_any(lowered, ("返回", "back")):
            steps.append(FlowStepDTO(action=FlowAction.back))
        elif _matches_any(lowered, ("滑动", "scroll", "swipe")):
            steps.append(FlowStepDTO(action=FlowAction.scroll))
        else:
            unmapped.append(line)

    if unmapped:
        warnings.append("Some testcase lines could not be mapped to controlled flow actions.")
    flow = SampleFlowDTO(
        name=test_name or "Uploaded testcase sample",
        platform=platform,
        package_name=package_name,
        generated_from="testcase_upload",
        requires_confirmation=True,
        steps=steps,
    )
    return flow, warnings, unmapped


def _case_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        normalized = re.sub(r"^\s*(?:[-*]|\d+[.)]|步骤\s*\d+[:：]?)\s*", "", line).strip()
        if normalized:
            lines.append(normalized)
    return lines[:100]


def _matches_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _extract_argument(line: str) -> str:
    value = re.sub(
        r"(?i)^\s*(点击|输入|看到|显示|断言|检查|tap(?:\s+on)?|click|input|type|assert|verify|expect)\s*[:：]?\s*",
        "",
        line,
    ).strip(" '\"`")
    return value or line[:80]


def _extract_wait_ms(line: str) -> int:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(ms|毫秒|s|秒)?", line, re.IGNORECASE)
    if not match:
        return 3000
    value = float(match.group(1))
    unit = (match.group(2) or "s").lower()
    if unit in {"ms", "毫秒"}:
        return max(100, int(value))
    return max(100, int(value * 1000))


def _content_type_for(extension: str) -> str:
    if extension == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if extension in {".md", ".markdown"}:
        return "text/markdown"
    return "text/plain"


BLOCK_PATTERNS = [
    ("authorization", re.compile(r"(?i)\bauthorization\s*[:=]\s*(?:bearer\s+)?[A-Za-z0-9._~+/=-]{8,}")),
    ("api_key", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?key)\s*[:=]\s*[A-Za-z0-9._~+/=-]{8,}")),
    ("token", re.compile(r"(?i)\b(?:token|cookie|sessionid)\s*[:=]\s*[A-Za-z0-9._~+/=-]{8,}")),
    ("password", re.compile(r"(?i)\b(?:password|passwd|pwd|secret)\s*[:=]\s*\S{4,}")),
    ("verification_code", re.compile(r"(?i)\b(?:验证码|verification\s*code|otp)\s*[:=：]?\s*\d{4,8}\b")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

REDACT_PATTERNS = [
    ("email", re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")),
    ("phone", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("id_card", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("bank_card", re.compile(r"(?<!\d)(?:\d[ -]?){16,19}(?!\d)")),
]
