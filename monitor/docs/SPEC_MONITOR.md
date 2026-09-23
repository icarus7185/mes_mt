# Service Specification — `monitor`

## Central Dashboard & Archive Service

| | |
|---|---|
| **Document type** | Service-level specification |
| **Service** | `monitor` |
| **Port** | 8003 |
| **Companion documents** | `SPEC_SYSTEM_OVERVIEW.md` (architecture & cross-service data flow) · `SPEC_PROD_LINE.md` · `SPEC_ASST.md` |
| **Version** | 1.0 |
| **Date** | 2026-09-23 |
| **Status** | Approved for baseline (reverse-documented) |
| **Prepared by** | Business Analyst (AI-assisted) |

> This spec is scoped to the `monitor` service only. For where its input comes from, see `SPEC_SYSTEM_OVERVIEW.md` §2–§3.

---

## 1. Purpose & role

`monitor` is the system's operator-facing "control room." It is the terminal node of both pipelines: it receives everything `asst` has already processed (confirmed defect images, completed energy predictions) and is responsible for archiving it, summarizing it, and presenting it on a single live dashboard. It is the only service with a permanent, unbounded data store (the CSV history) and the only one whose dashboard is intended for continuous operator use.

## 2. Responsibilities

- Archive every confirmed defect alert image, bounded to a fixed recent window.
- Receive every completed energy prediction, keep a bounded recent window for the live dashboard, and permanently log every one to disk.
- Present both streams — plus derived KPIs — on one auto-refreshing dashboard.
- Never lose a record's data due to a display-window limit: what falls off the in-memory grid remains in the permanent CSV log.

## 3. Functional requirements

### FR-M1 — Defect-alert image archive

- **Trigger:** `POST /api/image` (from `asst`).
- **Behavior:** Save the received image under `hist_dir` (default `monitor/data/img`).
- **Business rule:** After each save, delete the oldest file(s) beyond `hist_max_files` (default 10) so the archive never grows unbounded — a strict FIFO/most-recent-N retention policy.
- **Acceptance criteria:** After more than 10 alerts have been received, exactly the 10 most recent image files remain on disk; older ones are gone (not moved elsewhere).

### FR-M2 — Energy prediction history

- **Trigger:** `POST /api/record` (from `asst`).
- **Behavior:**
  1. Add the record to a bounded in-memory list (`record_max_items`, default 20; oldest entry evicted when the bound is exceeded), tagged with a `received_at` timestamp.
  2. Append a row to a permanent CSV log (`tabular_dir/records_history.csv`), writing a header row on first write.
- **Business rules:** The in-memory list feeds the live dashboard grid/chart/KPIs (fast, bounded, lost on restart). The CSV is the durable system of record (unbounded, append-only, survives restart) — the two do **not** need to agree in size or lifetime.
- **Acceptance criteria:** The in-memory grid never exceeds `record_max_items` entries; the CSV file contains every record ever received, in receipt order, and is still present and intact after a service restart.

### FR-M3 — Operator dashboard (`GET /`)

A single-page, auto-refreshing (2 s), English-language dashboard with the following panels:

1. **KPI stat tiles (4):**
   - Average predicted `Usage_kWh` over the last 20 in-memory records.
   - Trend vs. the previous record (▲/▼ signed delta).
   - Time since the last **new** record arrived, colour-coded green (≤ 60 s) / amber (≤ 180 s) / red (> 180 s) — a pipeline-staleness early warning.
   - Percentage of the currently-displayed records at `Maximum_Load`, colour-coded by severity (< 20% good, < 50% warning, ≥ 50% critical).
2. **Predicted power consumption grid** — scrollable table of recent records: Timestamp, sensor columns (Lagging/Leading kVarh, CO2, Lagging/Leading PF, NSM), Load Type as a colour-coded severity badge (green/amber/red for Light/Medium/Maximum), and the predicted `Usage_kWh` column visually distinguished (accent colour + left border) as the machine-predicted value. A newly-arrived top row briefly flashes to draw the eye.
3. **Line chart** — predicted `Usage_kWh` over time: gridlines, an end-of-line value label, and an interactive crosshair + tooltip on hover showing the exact timestamp and value.
4. **Defect alert panel** — the most recently archived alert image and its received time; click or keyboard-activate to open a full-size lightbox; shows a text placeholder (not a broken-image icon) when nothing has been received yet.
5. **Alert album** — thumbnails of the (up to 10) most recent archived alert images, each click/keyboard-activatable to open the same lightbox, with its own caption (filename + received time).

- **Business rules:**
  - Layout is a responsive 4-column grid: records grid (3 cols) + chart (1 col) on row 1; image panel + album (2 cols each) on row 2.
  - The UI supports both light and dark modes automatically, following the operating system's `prefers-color-scheme`.
  - The enlarged-image lightbox is closable via a close button, clicking outside the image, or the <kbd>Esc</kbd> key.
- **Acceptance criteria:** All panels refresh every 2 seconds without a full page reload; every stat tile and grid value is derived only from data the dashboard has already fetched (no additional round-trip per tile); clicking/activating any alert image opens an enlarged, captioned view that can be dismissed three different ways.

### FR-M4 — Historical image/record retrieval APIs

- **Description:** Supporting read endpoints consumed by the dashboard's own JavaScript, and available for external consumption if needed.
- **Acceptance criteria:** Each endpoint returns a well-formed response even when no data has been received yet (empty list / `null` fields rather than an error), except a specific missing image filename, which returns `404`.

## 4. Data

### 4.1 Data consumed

See `SPEC_SYSTEM_OVERVIEW.md` §3 for the canonical wire payload schemas `monitor` receives from `asst` (`POST /api/image`, `POST /api/record`).

### 4.2 Data added locally

| Field | Added on | Type | Meaning |
|---|---|---|---|
| `received_at` (in-memory grid) | `POST /api/record` | string `HH:MM:SS` | When `monitor` received the record, for dashboard display |
| `received_at` (CSV row) | `POST /api/record` | string `YYYY-MM-DD HH:MM:SS` | Full-precision receive timestamp for the permanent log |
| `received_at` (image) | `POST /api/image` | derived from file mtime, `HH:MM:SS` | When the archived image file was last written |

### 4.3 CSV history schema (`monitor/data/tabular/records_history.csv`)

Column order as written:

`received_at, date, Usage_kWh, Lagging_Current_Reactive.Power_kVarh, Leading_Current_Reactive_Power_kVarh, CO2(tCO2), Lagging_Current_Power_Factor, Leading_Current_Power_Factor, NSM, WeekStatus, Day_of_week, Load_Type`

### 4.4 Data retention

| Store | Bounded? | Survives restart? |
|---|---|---|
| Defect alert image archive (`hist_dir`) | Yes — most recent `hist_max_files` (default 10) | Yes (filesystem) |
| In-memory record grid | Yes — most recent `record_max_items` (default 20) | **No** — cleared on restart |
| `records_history.csv` | No — append-only, unbounded | Yes (filesystem) |

## 5. External interfaces

### 5.1 Inbound API — `http://localhost:8003`

| Method & Path | Purpose | Request | Response |
|---|---|---|---|
| `GET /` | Operator dashboard (HTML). | — | HTML |
| `POST /api/image` | Receive & archive a defect alert image from `asst`. | `multipart/form-data`, field `file` | `{"status": "ok"}` |
| `GET /api/image/latest` | Most recently archived alert image. | — | `image/jpeg`, or `404` if none yet |
| `GET /api/image/meta` | Metadata for the latest archived alert image. | — | `{"received_at": str\|null, "filename": str\|null}` |
| `GET /api/hist` | List of currently archived alert images (album), newest first. | — | `{"images": [ {"filename": str, "received_at": str}, ... ]}` |
| `GET /api/hist/{filename}` | Retrieve one archived alert image by filename. | — | `image/jpeg`, or `404` if not found |
| `POST /api/record` | Receive a predicted sensor record from `asst`. | JSON record (see `SPEC_SYSTEM_OVERVIEW.md` §3.2) | `{"status": "ok"}` |
| `GET /api/records` | Recent predicted records for the dashboard grid/chart (newest first, bounded to `record_max_items`). | — | `{"records": [ {...}, ... ]}` |

`monitor` makes **no outbound calls** to the other two services — it is a terminal node in both pipelines.

## 6. Configuration reference

| Setting | Default | Description |
|---|---|---|
| `hist_dir` | `monitor/data/img` | Defect alert image archive folder |
| `hist_max_files` | `10` | Max images retained in the archive |
| `record_max_items` | `20` | Max records kept in the in-memory dashboard grid |
| `tabular_dir` | `monitor/data/tabular` | Folder for the permanent `records_history.csv` |
| `host` / `port` | `0.0.0.0` / `8003` | Bind address |

## 7. Non-functional requirements

| ID | Requirement |
|---|---|
| M-NFR-1 | The dashboard polls every 2 seconds client-side; no server push (WebSocket/SSE) is used. |
| M-NFR-2 | The image archive and in-memory record grid are strictly bounded (FIFO eviction) so a long-running process does not grow memory/disk unbounded; the CSV history is the one intentionally unbounded store. |
| M-NFR-3 | The freshness KPI (time since last new record) is computed client-side against the timestamp of the most recently *seen* top-of-grid record, not against wall-clock "now," so it correctly reflects pipeline staleness rather than merely the time of the last successful poll. |
| M-NFR-4 | Interactive image elements (defect alert panel, album thumbnails) are keyboard-operable (`tabindex`, `Enter`/`Space` to activate) and carry accessible titles. |
| M-NFR-5 | The dashboard adapts to the operating system's light/dark theme automatically and remains usable down to narrow viewport widths. |
| M-NFR-6 | All file paths are relative to the process working directory — the service must be started from the repository root. |

## 8. Dependencies & assumptions

- `monitor` has no outbound dependency on either other service; it only receives inbound calls from `asst`.
- Assumes `asst` sends well-formed payloads matching the shared contract (`SPEC_SYSTEM_OVERVIEW.md` §3) — `monitor` does not independently validate or recompute anything `asst` has already produced (e.g. it does not re-run defect detection or re-predict `Usage_kWh`).
- The dashboard's KPI calculations (average, trend, load percentage) are computed **client-side in the browser** from the same `/api/records` response the grid uses — they are not separate server-side aggregates.

## 9. Directory layout

```
monitor/
├── config.py                    Settings (see §6)
├── main.py                      FastAPI app
├── routers/
│   ├── api.py                    All 8 endpoints (§5.1)
│   └── dashboard.py              GET / (FR-M3)
├── services/
│   ├── history_service.py        Image archive save + FIFO retention (FR-M1)
│   ├── record_service.py         In-memory bounded record grid (FR-M2)
│   └── record_csv_service.py     Permanent CSV history append (FR-M2)
├── templates/dashboard.html      Dashboard markup (stat tiles, grid, chart, image, album, lightbox)
├── static/                       Dashboard CSS/JS (incl. hand-drawn SVG chart & icons)
└── data/
    ├── img/                       Bounded defect-alert image archive
    └── tabular/                    records_history.csv (permanent log)
```
