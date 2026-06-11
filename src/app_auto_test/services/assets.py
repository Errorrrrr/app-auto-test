from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from fastapi import UploadFile

from ..schemas import ApkAssetDTO, new_id
from ..storage import JsonStore


class AssetService:
    def __init__(self, store: JsonStore):
        self.store = store

    async def save_apk(self, upload: UploadFile) -> ApkAssetDTO:
        asset_id = new_id("apk")
        safe_name = Path(upload.filename or f"{asset_id}.apk").name
        asset_dir = self.store.assets_dir / asset_id
        asset_dir.mkdir(parents=True, exist_ok=True)
        destination = asset_dir / safe_name
        sha256 = hashlib.sha256()
        size = 0
        with destination.open("wb") as fh:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                sha256.update(chunk)
                fh.write(chunk)

        package_name = self._try_read_package_name(destination)
        asset = ApkAssetDTO(
            asset_id=asset_id,
            file_name=safe_name,
            content_type=upload.content_type or "application/vnd.android.package-archive",
            size_bytes=size,
            sha256=sha256.hexdigest(),
            stored_path=str(destination),
            package_name=package_name,
        )
        return self.store.save_asset(asset)

    def _try_read_package_name(self, apk_path: Path) -> str | None:
        aapt = shutil.which("aapt") or shutil.which("aapt2")
        if not aapt:
            return None
        try:
            result = subprocess.run(
                [aapt, "dump", "badging", str(apk_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0:
            return None
        match = re.search(r"package: name='([^']+)'", result.stdout)
        return match.group(1) if match else None

