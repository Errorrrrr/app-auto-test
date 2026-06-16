from __future__ import annotations

import re


BLOCK_PATTERNS = [
    ("authorization", re.compile(r"(?i)\bauthorization\s*[:=]\s*(?:bearer\s+)?[A-Za-z0-9._~+/=-]{8,}")),
    ("api_key", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?key)\s*[:=]\s*[A-Za-z0-9._~+/=-]{8,}")),
    (
        "token",
        re.compile(
            r"(?i)\b(?:access[_-]?token|refresh[_-]?token|id[_-]?token|token)\s*[:=]\s*[A-Za-z0-9._~+/=-]{8,}"
        ),
    ),
    ("cookie", re.compile(r"(?i)\b(?:cookie|sessionid|session[_-]?id)\s*[:=]\s*[^\r\n]+")),
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
