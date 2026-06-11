# App Auto Test Backend

Backend foundation for the local app automation MVP.

The first stage is a Codex-only + Android local runner skeleton:

- upload an APK at test-run time
- list selectable Android devices or emulators
- generate an editable sample flow automatically
- create a local run with a controlled runner boundary
- write append-only run events
- generate reports that can be viewed in the tool or exported as HTML/JSON
- keep iOS in capability-check/blocked mode until signing inputs are supplied

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app_auto_test.main:app --reload
```

Open the console at `http://127.0.0.1:8000/`. API docs are available at
`http://127.0.0.1:8000/docs`.

The console supports APK upload during run creation, device or emulator
selection, sample flow generation, blocked capability display, run status,
report viewing and HTML/JSON export.

## Key API Surface

- `GET /api/v1/health`
- `GET /api/v1/devices?platform=android`
- `POST /api/v1/samples/generate`
- `POST /api/v1/assets/apk`
- `POST /api/v1/runs` with multipart fields and an APK file
- `GET /api/v1/runs`
- `POST /api/v1/runs/{run_id}/start`
- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/runs/{run_id}/events`
- `GET /api/v1/runs/{run_id}/report`
- `GET /api/v1/runs/{run_id}/report/export?format=html`

## Runtime Configuration

Environment variables:

- `APP_AUTO_TEST_DATA_DIR`: local data directory, default `.local-data`
- `APP_AUTO_TEST_ADB_PATH`: adb binary path, default `/Users/zxx/Library/Android/sdk/platform-tools/adb`
- `APP_AUTO_TEST_MAESTRO_BIN`: Maestro command, default `maestro`
- `APP_AUTO_TEST_ALLOW_REAL_EXECUTION`: must be `true` before the runner attempts real device execution

By default, real execution is disabled. The runner still performs capability checks and writes a blocked report with the exact missing inputs. This keeps the API safe while the frontend and tool contracts are integrated.

## Development

```bash
pytest
```

The test suite uses temporary data directories and does not require a connected Android device.
