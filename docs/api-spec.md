# API Specification

| | |
|---|---|
| **Project** | `mes_mt` |
| **Version** | 1.0 |
| **Date** | 2026-09-24 |
| **Source** | Written from the current source code (`*/main.py`, `*/routers/*.py`) |

The system has three independent FastAPI services. They call each other over plain HTTP. There is no authentication, and no API versioning.

| Service | Base URL | Routers |
|---|---|---|
| `prod_line` | `http://localhost:8001` | `prod_line/routers/dashboard.py`, `prod_line/routers/api.py` |
| `asst` | `http://localhost:8002` | `asst/routers/api.py` |
| `monitor` | `http://localhost:8003` | `monitor/routers/dashboard.py`, `monitor/routers/api.py` |

```
prod_line ──POST /api/image──►  asst ──POST /api/image──►  monitor
prod_line ──POST /api/record─►  asst ──POST /api/record─►  monitor
```

Each service also exposes FastAPI's built-in `GET /docs`, `GET /redoc` and `GET /openapi.json`. `prod_line` and `monitor` serve their CSS/JS under `GET /static/*`.

---

## 1. Common data: Record

`POST /api/record` (on `asst` and `monitor`) and `GET /api/records` (on `prod_line` and `monitor`) use a JSON object whose keys are the columns of `Steel_industry_data.csv`.

| Field | Type | Example |
|---|---|---|
| `date` | string `dd/mm/yyyy HH:MM:SS` | `"24/09/2026 10:15:03"` |
| `Usage_kWh` | number \| null | `null` (from `prod_line`), `3.42` (after `asst`) |
| `Lagging_Current_Reactive.Power_kVarh` | number | `2.95` |
| `Leading_Current_Reactive_Power_kVarh` | number | `0.0` |
| `CO2(tCO2)` | number | `0.0` |
| `Lagging_Current_Power_Factor` | number | `73.21` |
| `Leading_Current_Power_Factor` | number | `100.0` |
| `NSM` | integer | `900` |
| `WeekStatus` | string | `"Weekday"` |
| `Day_of_week` | string | `"Monday"` |
| `Load_Type` | string | `"Light_Load"` |

The endpoints take the body as a plain `dict`. No field is validated by schema: a request only needs a JSON object. A non-object body returns `422`.

Example:

```json
{
  "date": "24/09/2026 10:15:03",
  "Usage_kWh": null,
  "Lagging_Current_Reactive.Power_kVarh": 2.95,
  "Leading_Current_Reactive_Power_kVarh": 0.0,
  "CO2(tCO2)": 0.0,
  "Lagging_Current_Power_Factor": 73.21,
  "Leading_Current_Power_Factor": 100.0,
  "NSM": 900,
  "WeekStatus": "Weekday",
  "Day_of_week": "Monday",
  "Load_Type": "Light_Load"
}
```

---

## 2. `prod_line` (port 8001)

`prod_line` runs two background loops (`prod_line/main.py` `lifespan`) that call `asst`. Its own endpoints are read-only and used by its dashboard.

### 2.1 `GET /`

Renders `prod_line/templates/index.html`.

**Side effect:** calls `record_service.reset_random_position()`. The next record sent to `asst` starts from a new random row of the CSV.

| Status | Body |
|---|---|
| `200` | HTML |

### 2.2 `GET /api/image/latest`

Returns the image most recently picked by the image loop, sent or not.

| Status | Content-Type | Body |
|---|---|---|
| `200` | `image/jpeg` | raw image bytes |
| `404` | `application/json` | `{"detail": "No image sent yet"}` |

The Content-Type is always `image/jpeg`, even when the source file is `.png` or `.bmp`.

### 2.3 `GET /api/image/meta`

Metadata for the image in 2.2.

`200`:

```json
{ "sent_at": "10:15:03", "filename": "img_001.jpg", "success": true }
```

Before the first image is picked:

```json
{ "sent_at": null, "filename": null, "success": null }
```

| Field | Type | Meaning |
|---|---|---|
| `sent_at` | string `HH:MM:SS` \| null | When the image was picked/sent |
| `filename` | string \| null | Source file name |
| `success` | boolean \| null | `false` = simulated failure or HTTP error when sending to `asst` |

### 2.4 `GET /api/records`

Records read by the record loop, newest first, at most `record_max_items` (20). Kept in memory only.

`200`:

```json
{
  "records": [
    {
      "date": "24/09/2026 10:15:03",
      "Usage_kWh": null,
      "...": "other Record fields (section 1)",
      "added_at": "10:15:03",
      "send_success": true
    }
  ]
}
```

Before any record is read: `{"records": []}`.

| Extra field | Type | Meaning |
|---|---|---|
| `added_at` | string `HH:MM:SS` | When the record was added to the list |
| `send_success` | boolean | Whether the send to `asst` succeeded |

### 2.5 Outbound calls

| Loop | Interval | Call | Skipped when |
|---|---|---|---|
| `producer.py` `producer_loop` | `interval_seconds` (3 s) | `POST {asst_image_url}` multipart, field `file` = (`filename`, bytes, `image/jpeg`) | `random() < image_send_failure_rate` (0.1), or no image file found |
| `record_producer.py` `record_producer_loop` | `record_interval_seconds` (15 s) | `POST {asst_record_url}` JSON Record with `Usage_kWh = null` | `random() < record_send_failure_rate` (0.2) |

The HTTP client uses `timeout=10.0` and `trust_env=False`. Any `httpx.HTTPError`, including a non-2xx response, marks the send as failed. The response body from `asst` is not used.

---

## 3. `asst` (port 8002)

No dashboard. At startup (`asst/main.py` `lifespan`) it downloads and loads the YOLO model from Hugging Face Hub and creates a shared `httpx.AsyncClient` (`timeout=10.0`, `trust_env=False`) for calls to `monitor`.

### 3.1 `POST /api/image`

Runs YOLO defect detection on an image. If something is detected, the annotated image is forwarded to `monitor`.

**Request:** `multipart/form-data`

| Field | Type | Required |
|---|---|---|
| `file` | file | yes |

If the upload has no filename, `image.jpg` is used.

**Processing:**

1. Save the bytes to `asst/data/img_in/<filename>`.
2. Run YOLO (`conf = yolo_confidence_threshold` = 0.6, `imgsz = 1024`), then delete the input file.
3. No detection → return a "normal" response. Nothing is sent to `monitor`.
4. Detection → save the annotated image to `asst/data/img_out/<stem>_<HHMMSS><ext>`, then `POST {monitor_image_url}` (multipart, field `file`, JPEG bytes). If `monitor` returns 2xx, delete the output file.

**Responses:**

No detection, `200`:

```json
{ "status": "normal", "file": "img_001.jpg" }
```

Detection, `200`:

```json
{ "saved_as": "img_001_101503.jpg", "classes": ["scratch", "scratch"] }
```

`classes` holds one class name per detected box, so the same name can appear more than once. The names come from the YOLO model.

| Status | When |
|---|---|
| `422` | `file` missing |
| `500` | The image can't be decoded, or the call to `monitor` fails (connection error or non-2xx). In the second case the annotated file stays in `asst/data/img_out`. |

### 3.2 `POST /api/record`

Predicts `Usage_kWh` for a record, fills it in, and forwards the full record to `monitor`.

**Request:** `application/json`, a Record (section 1). `Usage_kWh` is ignored and can be `null`.

**Processing:**

1. `analyst_service.predict_one(record, analyst_model_path)` loads `asst/data/model/analyst_model.pkl` and predicts.
2. `record["Usage_kWh"]` is set to the prediction.
3. `POST {monitor_record_url}` with the updated record.

**Response:** `200`

```json
{ "status": "ok", "Usage_kWh": 3.4213 }
```

| Status | When |
|---|---|
| `422` | Body is not a JSON object |
| `500` | Model file missing (`FileNotFoundError`: call `GET /api/train` first) |
| `500` | A required feature column is missing (`ValueError`) |
| `500` | `WeekStatus` / `Day_of_week` / `Load_Type` has a value not seen during training |
| `500` | The call to `monitor` fails (connection error or non-2xx) |

Error handlers are not customized, so FastAPI's default response is returned for these errors (`500 Internal Server Error`).

### 3.3 `GET /api/train`

Trains the `Usage_kWh` regression model from `training_csv_path` (`asst/data/train/Steel_industry_data.csv`) and overwrites `analyst_model_path`.

This is a synchronous (`def`) handler, so FastAPI runs it in a thread pool. The request blocks until training finishes.

**Response:** `200`

```json
{
  "status": "success",
  "mse": 1.2345,
  "r2": 0.9987,
  "model_path": "asst\\data\\model\\analyst_model.pkl"
}
```

| Field | Type | Meaning |
|---|---|---|
| `mse` | number | Mean squared error on the 25% test split |
| `r2` | number | R² on the 25% test split |
| `model_path` | string | Saved model path (`str(Path)`, so separators follow the OS) |

| Status | When |
|---|---|
| `500` | Training CSV not found, or it has no `Usage_kWh` column |

### 3.4 Outbound calls

| Trigger | Call |
|---|---|
| `POST /api/image` with a detection | `POST {monitor_image_url}` (`http://localhost:8003/api/image`), multipart, field `file` |
| `POST /api/record` | `POST {monitor_record_url}` (`http://localhost:8003/api/record`), JSON Record |

---

## 4. `monitor` (port 8003)

The end of both pipelines. It makes no outbound calls.

### 4.1 `GET /`

Renders `monitor/templates/dashboard.html`. The page polls the endpoints below every 2 seconds.

| Status | Body |
|---|---|
| `200` | HTML |

### 4.2 `POST /api/image`

Stores an image in `hist_dir` (`monitor/data/img`). After each save, only the `hist_max_files` (10) newest files (by modification time) are kept; older files are deleted. A file with the same name is overwritten.

**Request:** `multipart/form-data`, field `file` (required). If the upload has no filename, `image.jpg` is used.

**Response:** `200`

```json
{ "status": "ok" }
```

| Status | When |
|---|---|
| `422` | `file` missing |

### 4.3 `GET /api/image/latest`

The newest stored image.

| Status | Content-Type | Body |
|---|---|---|
| `200` | `image/jpeg` | raw image bytes |
| `404` | `application/json` | `{"detail": "No image received yet"}` |

### 4.4 `GET /api/image/meta`

`200`:

```json
{ "received_at": "10:15:04", "filename": "img_001_101503.jpg" }
```

When no image is stored:

```json
{ "received_at": null, "filename": null }
```

`received_at` is the file's modification time, formatted `HH:MM:SS`.

### 4.5 `GET /api/hist`

All stored images, newest first (at most 10).

`200`:

```json
{
  "images": [
    { "filename": "img_001_101503.jpg", "received_at": "10:15:04" },
    { "filename": "img_007_101421.jpg", "received_at": "10:14:22" }
  ]
}
```

When there are none: `{"images": []}`.

### 4.6 `GET /api/hist/{filename}`

One stored image by filename.

| Path param | Type |
|---|---|
| `filename` | string |

| Status | Content-Type | Body |
|---|---|---|
| `200` | `image/jpeg` | raw image bytes |
| `404` | `application/json` | `{"detail": "Image not found"}`. The file doesn't exist, or the resolved path is outside `hist_dir`. |

### 4.7 `POST /api/record`

Stores a predicted record.

**Request:** `application/json`, a Record (section 1) with `Usage_kWh` filled in.

**Processing:**

1. Add a copy with `received_at` (`HH:MM:SS`) to the front of an in-memory list of at most `record_max_items` (20).
2. Append a row to `monitor/data/tabular/records_history.csv`, writing the header if the file is new. `received_at` is written as `YYYY-MM-DD HH:MM:SS`. Keys that aren't CSV columns are ignored; missing keys are written as empty cells.

CSV column order:

```
received_at, date, Usage_kWh, Lagging_Current_Reactive.Power_kVarh, Leading_Current_Reactive_Power_kVarh, CO2(tCO2), Lagging_Current_Power_Factor, Leading_Current_Power_Factor, NSM, WeekStatus, Day_of_week, Load_Type
```

**Response:** `200`

```json
{ "status": "ok" }
```

| Status | When |
|---|---|
| `422` | Body is not a JSON object |

### 4.8 `GET /api/records`

Records received in memory, newest first, at most 20. Cleared on restart.

`200`:

```json
{
  "records": [
    {
      "date": "24/09/2026 10:15:03",
      "Usage_kWh": 3.4213,
      "...": "other Record fields (section 1)",
      "received_at": "10:15:04"
    }
  ]
}
```

When there are none: `{"records": []}`.

---

## 5. Endpoint summary

| Service | Method | Path | Request | Success response |
|---|---|---|---|---|
| `prod_line` | GET | `/` | — | HTML |
| `prod_line` | GET | `/api/image/latest` | — | `image/jpeg` / `404` |
| `prod_line` | GET | `/api/image/meta` | — | `{sent_at, filename, success}` |
| `prod_line` | GET | `/api/records` | — | `{records: [...]}` |
| `asst` | POST | `/api/image` | multipart `file` | `{status, file}` or `{saved_as, classes}` |
| `asst` | POST | `/api/record` | JSON Record | `{status, Usage_kWh}` |
| `asst` | GET | `/api/train` | — | `{status, mse, r2, model_path}` |
| `monitor` | GET | `/` | — | HTML |
| `monitor` | POST | `/api/image` | multipart `file` | `{status}` |
| `monitor` | GET | `/api/image/latest` | — | `image/jpeg` / `404` |
| `monitor` | GET | `/api/image/meta` | — | `{received_at, filename}` |
| `monitor` | GET | `/api/hist` | — | `{images: [...]}` |
| `monitor` | GET | `/api/hist/{filename}` | — | `image/jpeg` / `404` |
| `monitor` | POST | `/api/record` | JSON Record | `{status}` |
| `monitor` | GET | `/api/records` | — | `{records: [...]}` |
