from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess

from ..config import Settings
from ..schemas import CapabilityDTO, DeviceDTO, DeviceKind, DeviceStatus, Platform


PACKAGE_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")
SAFE_DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")


class DeviceService:
    provider_name = "local-device"

    def __init__(self, settings: Settings):
        self.settings = settings

    def list_devices(self, platform: Platform = Platform.android) -> list[DeviceDTO]:
        if platform == Platform.ios:
            return self._list_ios_capability_placeholder()
        return self._list_android_devices()

    def check_android_capability(
        self,
        *,
        device_id: str | None,
        apk_path: str | None,
        package_name: str | None,
    ) -> CapabilityDTO:
        adb_config_safe = _safe_command_value(self.settings.adb_path)
        maestro_config_safe = _safe_command_value(self.settings.maestro_bin)
        adb = self.resolve_adb_command()
        devices = self._list_android_devices() if adb else []
        device_id_safe = bool(device_id and SAFE_DEVICE_ID_PATTERN.fullmatch(device_id))
        selected_device = (
            next((item for item in devices if item.id == device_id), None)
            if device_id_safe
            else None
        )
        adb_exists = adb is not None
        maestro_exists = self.resolve_maestro_command() is not None
        apk_present = bool(apk_path)
        apk_file_exists = bool(apk_path and Path(apk_path).is_file())
        package_present = bool(package_name)
        package_valid = bool(package_name and PACKAGE_NAME_PATTERN.fullmatch(package_name))
        ready = all(
            [
                adb_config_safe,
                adb_exists,
                maestro_config_safe,
                selected_device is not None,
                selected_device.selectable if selected_device else False,
                apk_present,
                apk_file_exists,
                package_present,
                package_valid,
                device_id_safe,
                maestro_exists,
                self.settings.allow_real_execution,
            ]
        )

        missing: list[str] = []
        blocked: list[str] = []
        actions: list[str] = []
        if not adb_config_safe:
            _append_unique(missing, "adb")
            blocked.append("ADB_COMMAND_UNSAFE")
            actions.append("Set APP_AUTO_TEST_ADB_PATH to a single executable path without control characters.")
        if not adb_exists:
            _append_unique(missing, "adb")
            blocked.append("ADB_NOT_FOUND")
            actions.append("Set APP_AUTO_TEST_ADB_PATH or add adb to PATH.")
        if not maestro_config_safe:
            _append_unique(missing, "maestro")
            blocked.append("MAESTRO_COMMAND_UNSAFE")
            actions.append("Set APP_AUTO_TEST_MAESTRO_BIN to a single command or executable path without control characters.")
        if not device_id:
            _append_unique(missing, "deviceId")
            blocked.append("ANDROID_DEVICE_NOT_SELECTED")
            actions.append("Select one online Android device or emulator in the tool.")
        elif not device_id_safe:
            blocked.append("ANDROID_DEVICE_ID_INVALID")
            actions.append("Use a deviceId containing only letters, numbers, dot, underscore, colon or hyphen.")
        elif not selected_device:
            blocked.append("ANDROID_DEVICE_NOT_FOUND")
            actions.append("Select one online Android device or emulator in the tool.")
        elif not selected_device.selectable:
            blocked.append("ANDROID_DEVICE_NOT_ONLINE")
            actions.append("Start the selected emulator or reconnect the Android device.")
        if not apk_present:
            _append_unique(missing, "apk")
            blocked.append("APK_MISSING")
            actions.append("Upload an APK when creating the test run.")
        elif not apk_file_exists:
            blocked.append("APK_FILE_NOT_FOUND")
            actions.append("Re-upload the APK; the stored file is missing from the local data directory.")
        if not package_present:
            _append_unique(missing, "packageName")
            blocked.append("PACKAGE_NAME_MISSING")
            actions.append("Provide packageName or install aapt so it can be inferred.")
        elif not package_valid:
            blocked.append("PACKAGE_NAME_INVALID")
            actions.append("Provide a valid Android packageName such as com.example.app.")
        if not maestro_exists:
            _append_unique(missing, "maestro")
            blocked.append("MAESTRO_NOT_FOUND")
            actions.append("Install Maestro or configure APP_AUTO_TEST_MAESTRO_BIN.")
        if not self.settings.allow_real_execution:
            blocked.append("REAL_EXECUTION_DISABLED")
            actions.append("Set APP_AUTO_TEST_ALLOW_REAL_EXECUTION=true after reviewing runner permissions.")

        return CapabilityDTO(
            platform=Platform.android,
            ready=ready,
            checks={
                "adbCommandSafe": adb_config_safe,
                "adbAvailable": adb_exists,
                "maestroCommandSafe": maestro_config_safe,
                "deviceSelected": selected_device is not None,
                "deviceOnline": bool(selected_device and selected_device.selectable),
                "deviceIdSafe": device_id_safe,
                "apkUploaded": apk_present,
                "apkFileExists": apk_file_exists,
                "packageNameProvided": package_present,
                "packageNameValid": package_valid,
                "maestroAvailable": maestro_exists,
                "realExecutionEnabled": self.settings.allow_real_execution,
            },
            missing_fields=missing,
            blocked_reasons=blocked,
            next_actions=actions,
        )

    def check_ios_capability(self) -> CapabilityDTO:
        xcrun = shutil.which("xcrun")
        simctl_available = False
        simulator_available = False
        if xcrun:
            try:
                result = subprocess.run(
                    [xcrun, "simctl", "list", "devices", "available"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                simctl_available = result.returncode == 0
                simulator_available = "Booted" in result.stdout or "Shutdown" in result.stdout
            except (OSError, subprocess.SubprocessError):
                simctl_available = False

        return CapabilityDTO(
            platform=Platform.ios,
            ready=False,
            checks={
                "xcodeAvailable": bool(xcrun),
                "simctlAvailable": simctl_available,
                "simulatorAvailable": simulator_available,
                "iosArtifactProvided": False,
                "bundleIdProvided": False,
                "signingReady": False,
                "deviceAvailable": False,
            },
            missing_fields=["ipa", "bundleId", "signingProfile", "targetDevice"],
            blocked_reasons=[
                "IOS_ARTIFACT_MISSING",
                "IOS_BUNDLE_ID_MISSING",
                "IOS_SIGNING_MISSING",
            ],
            next_actions=[
                "Provide IPA, bundleId, signing method and a target iOS device or simulator before real iOS execution.",
            ],
        )

    def resolve_adb_command(self) -> str | None:
        if not _safe_command_value(self.settings.adb_path):
            return None
        if shutil.which(self.settings.adb_path):
            return self.settings.adb_path
        return shutil.which("adb")

    def resolve_maestro_command(self) -> str | None:
        if not _safe_command_value(self.settings.maestro_bin):
            return None
        return shutil.which(self.settings.maestro_bin)

    def _list_android_devices(self) -> list[DeviceDTO]:
        adb = self.resolve_adb_command()
        if not adb:
            return [
                DeviceDTO(
                    id="android-adb-unavailable",
                    platform=Platform.android,
                    name="ADB unavailable",
                    kind=DeviceKind.unknown,
                    status=DeviceStatus.unavailable,
                    selectable=False,
                    blocked_reason="ADB_NOT_FOUND",
                )
            ]
        try:
            result = subprocess.run(
                [adb, "devices", "-l"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return [
                DeviceDTO(
                    id="android-adb-error",
                    platform=Platform.android,
                    name="ADB command failed",
                    kind=DeviceKind.unknown,
                    status=DeviceStatus.unavailable,
                    selectable=False,
                    blocked_reason="ADB_COMMAND_FAILED",
                )
            ]

        devices: list[DeviceDTO] = []
        for line in result.stdout.splitlines()[1:]:
            if not line.strip():
                continue
            parts = line.split()
            serial = parts[0]
            state = parts[1] if len(parts) > 1 else "unknown"
            kind = DeviceKind.emulator if serial.startswith("emulator-") else DeviceKind.physical
            selectable = state == "device"
            status = DeviceStatus.online if selectable else DeviceStatus.offline
            devices.append(
                DeviceDTO(
                    id=serial,
                    platform=Platform.android,
                    name=serial,
                    kind=kind,
                    status=status,
                    serial=serial,
                    selectable=selectable,
                    blocked_reason=None if selectable else f"ADB_STATE_{state.upper()}",
                )
            )
        if devices:
            return devices
        return [
            DeviceDTO(
                id="android-no-device",
                platform=Platform.android,
                name="No online Android device",
                kind=DeviceKind.unknown,
                status=DeviceStatus.unavailable,
                selectable=False,
                blocked_reason="ANDROID_DEVICE_NOT_FOUND",
            )
        ]

    def _list_ios_capability_placeholder(self) -> list[DeviceDTO]:
        capability = self.check_ios_capability()
        return [
            DeviceDTO(
                id="ios-blocked",
                platform=Platform.ios,
                name="iOS execution blocked",
                kind=DeviceKind.simulator,
                status=DeviceStatus.unavailable,
                selectable=False,
                blocked_reason=",".join(capability.blocked_reasons),
            )
        ]


def _safe_command_value(value: str) -> bool:
    candidate = value.strip()
    if not candidate:
        return False
    return not any(char in candidate for char in ("\r", "\n", "\x00"))


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
