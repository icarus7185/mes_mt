# Service Specification — `prod_line`

## Line Simulation & Producer Service

| | |
|---|---|
| **Document type** | Service-level specification |
| **Service** | `prod_line` |
| **Port** | 8001 |
| **Companion documents** | `SPEC_SYSTEM_OVERVIEW.md` (architecture & cross-service data flow) · `SPEC_ASST.md` · `SPEC_MONITOR.md` |
| **Version** | 1.0 |
| **Date** | 2026-09-23 |
| **Status** | Approved for baseline (reverse-documented) |
| **Prepared by** | Business Analyst (AI-assisted) |

> This spec is scoped to the `prod_line` service only. For how its output is consumed downstream, see `SPEC_SYSTEM_OVERVIEW.md` §2–§3.

---

## 1. Purpose & role

`prod_line` simulates the physical production line's data acquisition layer: a camera capturing surface images, and sensors reporting electrical/energy readings. In the absence of real hardware, it draws from static sample assets on a timer and pushes readings downstream to `asst` for AI processing. It also hosts a small operator-facing dashboard so a line engineer can verify, in real time, what is being captured and whether it is successfully reaching the next service.

## 2. Responsibilities

- Periodically select and transmit a simulated camera image.
- Periodically select and transmit a simulated sensor reading (from a historical energy dataset), stamped with the current time.
- Simulate a configurable rate of transmission failure on each of the above, independent of whether the downstream service is actually reachable.
- Always reflect the latest captured reading — and its transmission outcome — on its own dashboard, regardless of whether the send succeeded.
- Never block or crash the simulation loop on a single failed send.

## 3. Functional requirements

### FR-P1 — Simulated camera image capture & transmission

- **Trigger:** Background timer, every `interval_seconds` (default 3 s).
- **Behavior:** Randomly select one eligible image file (`.jpg`, `.jpeg`, `.png`, `.bmp`) from `image_in_dir` and attempt to send it to `asst` via `POST /api/image` (multipart upload).
- **Business rules:**
  - If the source folder has no eligible image files, the attempt is skipped and a warning is logged; no dashboard state changes.
  - Every attempt — sent or not — updates the "last sent image" state (image bytes, filename, timestamp, Success/Failed outcome) so the dashboard always reflects the most recent simulated reading.
- **Acceptance criteria:** Given at least one image file exists, an image is picked and either transmitted or marked failed at every tick of `interval_seconds`; the dashboard's image panel updates accordingly within one refresh cycle.

### FR-P2 — Simulated sensor record capture & transmission

- **Trigger:** Background timer, every `record_interval_seconds` (default 15 s).
- **Behavior:** Read the **next row** of the tabular dataset (`tabular_csv_path`) and attempt to send it to `asst` via `POST /api/record` (JSON).
- **Business rules:**
  - **Reading position** starts at a random row when the service starts, and re-randomizes every time the `prod_line` index page (`GET /`) is loaded — giving a fresh "random walk" per dashboard view.
  - Each subsequent read advances the cursor by `record_skip` rows (default 2), wrapping around to the start of the dataset at the end.
  - Before sending, the row's `date` field is overwritten with the current server time (`dd/mm/yyyy HH:MM:SS`), and its `Usage_kWh` value is cleared (`null`) — `asst` is responsible for predicting it.
  - The record is pushed onto the in-memory dashboard grid **immediately upon being read**, tagged with a local `added_at` timestamp and the eventual `send_success` outcome — independent of whether the transmission to `asst` succeeds (see FR-P3).
- **Acceptance criteria:** Each transmitted record carries a fresh timestamp and a null `Usage_kWh`; reading position advances deterministically by `record_skip` between dashboard loads and re-randomizes on each load; the record appears on the dashboard grid even when the send fails.

### FR-P3 — Simulated transmission failure (overload simulation)

- **Trigger:** Evaluated independently on every image send (FR-P1) and every record send (FR-P2).
- **Behavior:** Before attempting the real HTTP call, roll a random probability against a configurable failure rate:
  - `image_send_failure_rate` (default 0.1 = 10%)
  - `record_send_failure_rate` (default 0.2 = 20%)
- **Business rules:**
  - If the roll indicates failure: the HTTP call is **not attempted** (simulated overload/drop); the reading is tagged `Failed`.
  - If the roll indicates success but the real HTTP call still errors (e.g. `asst` unreachable or times out): the reading is also tagged `Failed`.
  - Otherwise: the reading is tagged `Success`.
  - In every case, the reading is still captured and displayed with its outcome — nothing is ever silently dropped from the operator's view.
- **Acceptance criteria:** Over a large number of ticks, the observed failure rate for each stream converges to its configured probability (plus any genuine network failures); every reading shown on the dashboard carries an explicit Success/Failed status.

### FR-P4 — Operator dashboard (`GET /`)

- **Behavior:** A single-page, auto-refreshing (2 s) English-language dashboard showing:
  1. The most recently captured camera image, its send time, and a Success/Failed status badge.
  2. A scrollable grid of the most recent sensor records (bounded to `record_max_items`, default 20), newest first, with two-line column headers: Timestamp, Send Status (badge), Lagging kVarh, Leading kVarh, CO2, Lagging PF, Leading PF, NSM, Load Type.
- **Business rule:** Loading/reloading the page re-randomizes the sensor-record reading position (see FR-P2).
- **Acceptance criteria:** The grid and image panel refresh automatically without a manual page reload; Success/Failed badges are visually distinct (green/red).

## 4. Data

### 4.1 Data produced

See `SPEC_SYSTEM_OVERVIEW.md` §3.2 for the canonical wire payload schema. `prod_line` is the **originator** of every field in that schema except `Usage_kWh` (which it always sends as `null`).

Locally (dashboard-only, not sent on the wire):

| Field | Type | Meaning |
|---|---|---|
| `added_at` | string `HH:MM:SS` | When the row was read into the local dashboard grid |
| `send_success` | boolean | Outcome of the transmission attempt (FR-P3) |

For the image stream, `prod_line` sends the raw image bytes as-is (`multipart/form-data`, field `file`) with the original filename.

### 4.2 Data source

- `image_in_dir` (default `prod_line/data/from_camera/`) — pool of sample images the camera simulator draws from.
- `tabular_csv_path` (default `prod_line/data/tabular/Steel_industry_data.csv`) — source dataset for the sensor simulator (schema in `SPEC_SYSTEM_OVERVIEW.md` §3.1).

### 4.3 Data retention

All `prod_line` state is **in-memory only** and is lost on restart:

- Last sent image (bytes, filename, timestamp, outcome).
- Recent sensor records grid, bounded to `record_max_items` (FIFO eviction).

`prod_line` does not write any output data files; it only writes to its log file.

## 5. External interfaces

### 5.1 Inbound API — `http://localhost:8001`

| Method & Path | Purpose | Response |
|---|---|---|
| `GET /` | Operator dashboard (HTML). Re-randomizes the sensor-record reading position on every load. | HTML |
| `GET /api/image/latest` | Most recently captured/sent image (raw JPEG bytes). | `image/jpeg`, or `404` if none yet |
| `GET /api/image/meta` | Metadata for the latest image. | `{"sent_at": str\|null, "filename": str\|null, "success": bool\|null}` |
| `GET /api/records` | Recent sensor records read for transmission (newest first, bounded to `record_max_items`). | `{"records": [ {...}, ... ]}` |

### 5.2 Outbound calls (`prod_line` → `asst`)

| Call | Target | Trigger |
|---|---|---|
| `POST /api/image` | `asst_image_url` (default `http://localhost:8002/api/image`) | FR-P1, every `interval_seconds` |
| `POST /api/record` | `asst_record_url` (default `http://localhost:8002/api/record`) | FR-P2, every `record_interval_seconds` |

## 6. Configuration reference

| Setting | Default | Description |
|---|---|---|
| `image_in_dir` | `prod_line/data/from_camera` | Source folder for simulated camera images |
| `interval_seconds` | `3.0` | Seconds between image captures |
| `asst_image_url` | `http://localhost:8002/api/image` | Target endpoint for image transmission |
| `image_send_failure_rate` | `0.1` | Probability [0, 1] an image send is simulated as failing |
| `tabular_csv_path` | `prod_line/data/tabular/Steel_industry_data.csv` | Source CSV for simulated sensor records |
| `record_interval_seconds` | `15.0` | Seconds between sensor-record captures |
| `asst_record_url` | `http://localhost:8002/api/record` | Target endpoint for record transmission |
| `record_send_failure_rate` | `0.2` | Probability [0, 1] a record send is simulated as failing |
| `record_skip` | `2` | Rows advanced between consecutive record reads |
| `record_max_items` | `20` | Max records kept in the dashboard grid |
| `host` / `port` | `0.0.0.0` / `8001` | Bind address |

## 7. Non-functional requirements

| ID | Requirement |
|---|---|
| P-NFR-1 | Each background loop (image, record) catches and logs any exception per tick and continues on the next scheduled tick — a single failed send never stops the simulation. |
| P-NFR-2 | Image and record capture run on **independent** timers and are not coupled to each other or to dashboard page views (except that a page view re-randomizes the record cursor). |
| P-NFR-3 | The dashboard polls every 2 seconds client-side; no server push (WebSocket/SSE) is used. |
| P-NFR-4 | All file paths are relative to the process working directory — the service must be started from the repository root. |

## 8. Dependencies & assumptions

- Depends on `asst` being reachable at `asst_image_url` / `asst_record_url` for successful transmissions; `prod_line` itself starts and runs independently of `asst`'s availability (failed sends are simply marked `Failed`).
- Assumes `image_in_dir` and `tabular_csv_path` exist and are non-empty at runtime; an empty/missing image folder degrades gracefully (skipped tick, warning logged), but a missing/malformed CSV will raise an error at service startup (the dataset is loaded once, eagerly).
- No outbound dependency on `monitor` — `prod_line` never talks to `monitor` directly (see `SPEC_SYSTEM_OVERVIEW.md`).

## 9. Directory layout

```
prod_line/
├── config.py              Settings (see §6)
├── main.py                FastAPI app, background task lifespan wiring
├── producer.py             Image capture/send loop (FR-P1, FR-P3)
├── record_producer.py      Sensor record capture/send loop (FR-P2, FR-P3)
├── state.py                In-memory "last sent image" holder
├── record_state.py         In-memory bounded sensor-record grid
├── routers/
│   ├── api.py               GET endpoints (§5.1)
│   └── dashboard.py         GET / (FR-P4), re-randomizes record cursor
├── services/
│   ├── image_service.py     Random image file selection
│   └── record_service.py    Sequential/random-start CSV row walker (FR-P2)
├── templates/index.html      Dashboard markup
├── static/                   Dashboard CSS/JS
└── data/
    ├── from_camera/           Sample image pool
    └── tabular/                Source CSV
```
