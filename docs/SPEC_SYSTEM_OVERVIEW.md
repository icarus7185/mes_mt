# System Integration Specification

## MES Monitoring System — Cross-Service Architecture & End-to-End Data Flow

| | |
|---|---|
| **Document type** | System integration spec (links the 3 service-level specs together) |
| **Companion documents** | `SPEC_PROD_LINE.md` · `SPEC_ASST.md` · `SPEC_MONITOR.md` (per-service specs) · `BUSINESS_REQUIREMENTS.md` (business-level BRD) |
| **Project / Repository** | `mes_mt` |
| **Version** | 1.0 |
| **Date** | 2026-09-23 |
| **Status** | Approved for baseline (reverse-documented) |
| **Prepared by** | Business Analyst (AI-assisted) |

> **Purpose of this document.** The technical specification is split into four spec-level documents so each microservice can be read, maintained, and handed to a service-owning team independently. **This document is the "glue"**: it does not repeat each service's internal business rules — those live in the three companion service specs — but it defines how the services fit together: the architecture, the two end-to-end pipelines, the shared data contract they all speak, and the cross-cutting concerns that apply to the system as a whole. No source code was changed to produce this document.

### Document map

| If you need... | Read... |
|---|---|
| How the 3 services are wired together, ports, and the shared payload contract | **This document** |
| `prod_line`'s own behavior, API, and configuration | `SPEC_PROD_LINE.md` |
| `asst`'s own behavior, API, and configuration | `SPEC_ASST.md` |
| `monitor`'s own behavior, API, and configuration | `SPEC_MONITOR.md` |
| Business goals / customer intent | `BUSINESS_REQUIREMENTS.md` |

---

## 1. System architecture

Three independent **FastAPI** applications, each with its own HTTP port, its own background scheduler (where applicable), its own web dashboard, and its own log file. There is no shared database, message broker, or shared process — all inter-service communication is **synchronous HTTP (REST/JSON or multipart file upload)**.

```
prod_line  --HTTP-->  asst  --HTTP-->  monitor
(producer)            (AI/ML worker)   (dashboard)
   :8001                 :8002             :8003
```

| Service | Port | Role | Spec |
|---|---|---|---|
| `prod_line` | 8001 | Simulates the physical line: picks images/sensor rows and pushes them downstream on a timer. Hosts an operator UI showing what was just sent. | `SPEC_PROD_LINE.md` |
| `asst` | 8002 | Stateless AI/ML worker: runs YOLO defect detection on images, and a trained regression model on sensor records. Forwards results to `monitor`. | `SPEC_ASST.md` |
| `monitor` | 8003 | Central dashboard: archives defect alert images, keeps a rolling grid + line chart of predicted energy usage, persists a full history CSV. | `SPEC_MONITOR.md` |

All three are started independently (see Appendix B) and discover each other only via **hardcoded base URLs** in each service's own configuration (e.g. `asst.config.settings.monitor_image_url`) — there is no service registry or discovery mechanism.

---

## 2. End-to-end pipelines

The system runs **two parallel pipelines** through the same three services, plus one cross-cutting behavior that applies to both.

### 2.1 Pipeline A — Surface defect detection (image stream)

```
prod_line/data/from_camera/*.jpg
        │ (random pick, every interval_seconds)
        ▼
POST /api/image  ────────────────►  asst
                                       │ YOLO inference (conf ≥ threshold)
                                       │
                     no detection ◄────┼────► detection found
                     (log only,                    │
                      nothing forwarded)      save to asst/data/img_out/
                                               POST /api/image
                                                     ▼
                                                  monitor
                                          archives into monitor/data/img
                                          (max 10 most recent, FIFO purge)
```

**Step-by-step lifecycle of one image:**

1. `prod_line` selects a random image file and either sends it or simulates a failure (§2.3).
2. If sent, `asst` receives it at `POST /api/image`, saves it temporarily, and runs YOLO inference.
3. **No detection above the confidence threshold:** `asst` deletes the temp file and logs the result. The pipeline stops here — `monitor` never sees this image.
4. **Detection found:** `asst` saves an annotated copy, deletes the original temp file, and forwards the annotated image to `monitor` at `POST /api/image`. Once forwarded, `asst` deletes its own copy too — `asst` never retains images.
5. `monitor` archives the received image under a bounded, FIFO-purged folder (max 10 files) and it becomes visible on the `monitor` dashboard (latest alert + album) immediately.

Full behavioral detail: `SPEC_PROD_LINE.md` §"Image capture" · `SPEC_ASST.md` §"Defect detection" · `SPEC_MONITOR.md` §"Image archive".

### 2.2 Pipeline B — Energy usage prediction (tabular/sensor stream)

```
prod_line/data/tabular/Steel_industry_data.csv
        │ (sequential read from a random start row, step = record_skip,
        │  every record_interval_seconds; Usage_kWh cleared, date stamped "now")
        ▼
POST /api/record  ──────────────►  asst
                                       │ ML regression model predicts Usage_kWh
                                       │ fills it into the record
                                       ▼
                                  POST /api/record
                                       ▼
                                    monitor
                     stores in a bounded in-memory grid (max record_max_items)
                     appends a row to monitor/data/tabular/records_history.csv
```

**Step-by-step lifecycle of one record:**

1. `prod_line` reads the next row from the source CSV (position starts random, then advances by `record_skip` rows per tick; re-randomizes whenever the `prod_line` dashboard is loaded), overwrites `date` with the current timestamp, and sets `Usage_kWh` to `null`.
2. `prod_line` either sends the record or simulates a failure (§2.3); **either way**, the record — with its own local `added_at` timestamp and `send_success` outcome — is pushed onto the `prod_line` dashboard grid immediately.
3. If sent, `asst` receives it at `POST /api/record`, derives model features from it (excluding `date`), and predicts `Usage_kWh`.
4. `asst` fills the predicted value into the record and forwards the **complete** record to `monitor` at `POST /api/record`.
5. `monitor` adds a `received_at` timestamp, stores the record in a bounded in-memory grid (used by the dashboard grid and chart), and appends a row to the permanent `records_history.csv`.

Full behavioral detail: `SPEC_PROD_LINE.md` §"Sensor record capture" · `SPEC_ASST.md` §"Energy usage prediction" · `SPEC_MONITOR.md` §"Energy prediction history".

### 2.3 Pipeline C — Simulated transmission failure (cross-cutting)

Applies independently to **both** sends `prod_line` performs (image and record):

```
prod_line picks a reading
        │
        ├── roll random probability < failure_rate ─► mark "Failed", do NOT call asst
        │
        └── otherwise call asst; a real network/HTTP error is also marked "Failed"

Regardless of outcome:
  • the reading is always captured and shown on the prod_line dashboard
  • the outcome (Success/Failed) is always shown alongside it
```

This is the mechanism by which the system demonstrates resilience/visibility against an unreliable plant network, **without** requiring a real unreliable network — see `SPEC_PROD_LINE.md` for the exact configuration knobs (`image_send_failure_rate`, `record_send_failure_rate`).

---

## 3. Shared data contract

Because there is no shared database or schema registry, the JSON payload exchanged between `prod_line` → `asst` → `monitor` **is** the contract. Any change to these field names must be coordinated across all three services simultaneously.

### 3.1 Source dataset schema (`Steel_industry_data.csv`)

Used both as the live "sensor feed" source (by `prod_line`) and as the ML training set (by `asst`). ~35,040 rows (15-minute interval readings).

| Column (raw CSV) | Type | Description |
|---|---|---|
| `date` | string (`dd/mm/yyyy HH:MM`) | Original dataset timestamp (superseded with the live send time before transmission) |
| `Usage_kWh` | float | Active energy consumption — the **prediction target** |
| `Lagging_Current_Reactive.Power_kVarh` | float | Lagging reactive power |
| `Leading_Current_Reactive_Power_kVarh` | float | Leading reactive power |
| `CO2(tCO2)` | float | Associated CO2 emissions |
| `Lagging_Current_Power_Factor` | float | Lagging power factor (%) |
| `Leading_Current_Power_Factor` | float | Leading power factor (%) |
| `NSM` | integer | Number of seconds from midnight |
| `WeekStatus` | categorical | `Weekday` / `Weekend` |
| `Day_of_week` | categorical | Day name |
| `Load_Type` | categorical | `Light_Load` / `Medium_Load` / `Maximum_Load` |

### 3.2 Wire payload — `POST /api/record` (both hops: `prod_line`→`asst` and `asst`→`monitor`)

Field names on the wire are the **raw CSV column names** above (the `Lagging_Reactive_Power_kVarh`-style renames used internally by `asst`'s model are a modelling convenience only — see `SPEC_ASST.md`).

| Field | Type | Set by | Notes |
|---|---|---|---|
| `date` | string | `prod_line` | Overwritten with current time, `dd/mm/yyyy HH:MM:SS` |
| `Usage_kWh` | float \| null | `prod_line` (null) → `asst` (filled) | Cleared by `prod_line`, predicted by `asst` |
| `Lagging_Current_Reactive.Power_kVarh` | float | `prod_line` | Passed through unchanged by `asst` |
| `Leading_Current_Reactive_Power_kVarh` | float | `prod_line` | Passed through unchanged |
| `CO2(tCO2)` | float | `prod_line` | Passed through unchanged |
| `Lagging_Current_Power_Factor` | float | `prod_line` | Passed through unchanged |
| `Leading_Current_Power_Factor` | float | `prod_line` | Passed through unchanged |
| `NSM` | integer | `prod_line` | Passed through unchanged |
| `WeekStatus` | string | `prod_line` | Passed through unchanged |
| `Day_of_week` | string | `prod_line` | Passed through unchanged |
| `Load_Type` | string | `prod_line` | Passed through unchanged |

Fields added **locally** by a service for its own dashboard (never required on the wire by the next hop):

| Field | Added by | Purpose |
|---|---|---|
| `added_at` | `prod_line` | When the row was read into the local dashboard grid |
| `send_success` | `prod_line` | Outcome of the transmission attempt (Pipeline C) |
| `received_at` | `monitor` | When `monitor` received the record |

### 3.3 Wire payload — `POST /api/image`

`multipart/form-data` with a single field `file` (the image bytes). No JSON schema; filename convention is the only metadata carried (original filename for `prod_line`→`asst`, original stem + `HHMMSS` suffix for `asst`→`monitor`, see `SPEC_ASST.md`).

---

## 4. Cross-cutting (system-wide) non-functional requirements

These apply to more than one service and are therefore defined once here; service-specific NFRs live in each service's own spec.

| ID | Requirement |
|---|---|
| SYS-NFR-1 | All three dashboards refresh client-side every 2 seconds, giving near-real-time visibility without WebSockets. |
| SYS-NFR-2 | Each service writes its own timestamped log file under `logs/` (`prod_line.log`, `asst.log`, `monitor.log`) in addition to console output. |
| SYS-NFR-3 | All configuration is centralized per service in a `Settings` object (`config.py`) with hardcoded defaults — there is currently no environment-variable/`.env` override layer, and no configuration is shared or synchronized between services beyond each one's own hardcoded URL to the next hop. |
| SYS-NFR-4 | All three UIs are English-language, with industry-standard electrical/energy terminology preserved (`kVarh`, `PF`, `CO2`, `NSM`, `Load Type`, `Usage_kWh`). |
| SYS-NFR-5 | Every service must be started from the **repository root** — all configured file paths are relative to the current working directory, not to the service's own package location. |
| SYS-NFR-6 | No authentication, authorization, or transport encryption (TLS) is implemented between services or on any dashboard. |
| SYS-NFR-7 | No shared database exists; state is either in-process memory (cleared on restart) or local files (survive restart). Each service's own spec states which of its data is durable. |
| SYS-NFR-8 | The system is designed for a **single instance of each service**; running multiple replicas of any service is not supported (in-memory state would diverge). |

---

## 5. System-wide assumptions, constraints & out of scope

These apply across service boundaries; see each service spec for anything service-specific.

- The three services are assumed reachable from one another over plain HTTP on `localhost`; no TLS, service discovery, or load balancing.
- `asst` requires outbound internet access on first startup to download YOLO weights from Hugging Face Hub (cached afterwards).
- `asst`'s `POST /api/record` requires a trained model artifact to already exist — an operator must call `GET /api/train` at least once after a fresh checkout, **before** Pipeline B can succeed end-to-end.
- Live categorical values (`WeekStatus`, `Day_of_week`, `Load_Type`) are assumed to be a subset of those seen during training; the fitted label encoders cannot encode unseen categories.
- Simulated send failures (Pipeline C) are the **only** fault-injection mechanism; there is no simulated latency, payload corruption, or out-of-order delivery.
- Out of scope system-wide: containerization/orchestration, CI/CD, multi-tenant access control, real PLC/SCADA/camera integration, push notifications/alerting channels, horizontal scaling, message queues, native mobile apps, automated test suite.

---

## Appendix A — Repository layout (top level)

```
mes_mt/
├── asst/            AI/ML worker service (port 8002)      → SPEC_ASST.md
├── monitor/         Central dashboard service (port 8003) → SPEC_MONITOR.md
├── prod_line/       Line simulation service (port 8001)   → SPEC_PROD_LINE.md
├── logs/            Per-service log files
├── docs/            Project documentation (this file and its companions)
├── requirements.txt Python dependency manifest (shared by all 3 services)
└── README.md        Developer quick-start guide
```

## Appendix B — How to run the whole system (development)

```bash
pip install -r requirements.txt

# in three separate terminals, from the repository root:
uvicorn monitor.main:app --port 8003
uvicorn asst.main:app --port 8002
uvicorn prod_line.main:app --port 8001

# one-time (or whenever the training dataset changes):
curl http://localhost:8002/api/train
```

Startup order does not strictly matter — `prod_line`'s background loops retry every tick, so a service that isn't up yet is simply skipped (and marked `Failed`) until it becomes reachable. However, Pipeline B will not succeed until `GET /api/train` has been called at least once against `asst`.

Then open:

- `http://localhost:8001/` — `prod_line` dashboard (what the line is capturing/sending right now)
- `http://localhost:8003/` — `monitor` dashboard (defect alerts + energy predictions)
