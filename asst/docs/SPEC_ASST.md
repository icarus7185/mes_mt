# Service Specification — `asst`

## AI/ML Worker Service

| | |
|---|---|
| **Document type** | Service-level specification |
| **Service** | `asst` |
| **Port** | 8002 |
| **Companion documents** | `SPEC_SYSTEM_OVERVIEW.md` (architecture & cross-service data flow) · `SPEC_PROD_LINE.md` · `SPEC_MONITOR.md` |
| **Version** | 1.0 |
| **Date** | 2026-09-23 |
| **Status** | Approved for baseline (reverse-documented) |
| **Prepared by** | Business Analyst (AI-assisted) |

> This spec is scoped to the `asst` service only. For where its input comes from and where its output goes, see `SPEC_SYSTEM_OVERVIEW.md` §2–§3.

---

## 1. Purpose & role

`asst` ("assistant") is the system's stateless AI/ML processing hub. It has no dashboard of its own and is never used directly by an operator — it exists purely to turn a raw camera image into a defect finding, and a raw sensor reading into an energy-usage prediction, then hand the enriched result to `monitor`. It hosts two independent, unrelated pieces of intelligence behind one FastAPI app:

1. A computer-vision model (YOLO) for **surface defect detection**.
2. A tabular regression model (XGBoost) for **energy usage prediction**.

## 2. Responsibilities

- Receive an uploaded image, run defect detection, and forward only genuine detections downstream — with no image left behind on `asst` itself.
- Receive a sensor record with a missing `Usage_kWh`, predict it, and forward the completed record downstream.
- Own the lifecycle of the energy-prediction model: load it for inference, and retrain it on demand.
- Never persist a request beyond what's needed to process and forward it (image temp files are deleted as soon as they're no longer needed).

## 3. Functional requirements

### FR-A1 — Surface defect detection (YOLO inference)

- **Trigger:** `POST /api/image` (from `prod_line`).
- **Behavior:** Save the uploaded image temporarily to `image_in_dir`, then run it through a YOLO segmentation model with a minimum confidence threshold (`yolo_confidence_threshold`, default 0.6). The model weights are pulled from Hugging Face Hub once, at service startup, and cached in memory for the life of the process.
- **Business rules:**
  - **No detection above threshold:** log the result, delete the temporary input file, and **forward nothing** to `monitor`. Response: `{"status": "normal", "file": <filename>}`.
  - **Detection found:** save the annotated image (boxes/segmentation drawn) to `image_out_dir`, delete the original temp input file, forward the annotated image to `monitor` via `POST /api/image`, and — once the forward succeeds — delete the local annotated copy too. Response: `{"saved_as": <filename>, "classes": [<detected class names>]}`.
- **Acceptance criteria:** An image with no qualifying defect never reaches `monitor`; an image with a qualifying defect reaches `monitor` exactly once, annotated, and leaves **no residual file** on `asst` afterward (success or failure of the forward call).

### FR-A2 — Energy usage prediction (`Usage_kWh`)

- **Trigger:** `POST /api/record` (from `prod_line`).
- **Behavior:** Accept a JSON sensor record with `Usage_kWh = null`, predict its value using the currently loaded regression model artifact, fill the value into the record, and forward the **completed** record to `monitor` via `POST /api/record`.
- **Business rules:**
  - The model artifact is loaded **fresh from disk on every prediction call** (not cached across requests in memory beyond the call), so a retrain (FR-A3) takes effect on the very next prediction without a service restart.
  - The predictive feature set is: `Lagging_Reactive_Power_kVarh`, `Leading_Reactive_Power_kVarh`, `CO2`, `Lagging_Power_Factor`, `Leading_Power_Factor`, `NSM`, `WeekStatus`, `Day_of_week`, `Load_Type` — renamed internally from the raw wire field names for modelling convenience (see §4.1).
  - The `date` field is **excluded** from the feature set: a live timestamp carries no generalizable predictive signal and would never match a value seen during training.
  - Categorical features (`WeekStatus`, `Day_of_week`, `Load_Type`) are transformed using label encoders that were fitted at training time; a value not seen during training will cause the prediction to fail.
  - Response: `{"status": "ok", "Usage_kWh": <predicted value>}`.
- **Acceptance criteria:** For a well-formed record whose categorical values were present in the training data, a numeric `Usage_kWh` prediction is always returned, filled into the record, and forwarded to `monitor` in the same request.

### FR-A3 — Model training (`GET /api/train`)

- **Trigger:** Manual, on-demand call (there is no scheduled/automatic retraining).
- **Behavior:** Load `training_csv_path` (default `asst/data/train/Steel_industry_data.csv`), split 75/25 train/test, fit an `XGBRegressor` against `Usage_kWh`, and persist the resulting artifact — model, feature column order, fitted categorical encoders — to `analyst_model_path` (default `asst/data/model/analyst_model.pkl`), overwriting any previous artifact.
- **Business rules:** `POST /api/record` (FR-A2) will fail with an error until this endpoint has been called at least once and produced a valid artifact file.
- **Acceptance criteria:** Response reports the resulting Mean Squared Error, R² score, and the saved model path: `{"status": "success", "mse": <float>, "r2": <float>, "model_path": <path>}`.

## 4. Data

### 4.1 Feature engineering rules (energy prediction)

| Raw wire field | Internal model feature name | Used as a feature? |
|---|---|---|
| `Lagging_Current_Reactive.Power_kVarh` | `Lagging_Reactive_Power_kVarh` | Yes |
| `Leading_Current_Reactive_Power_kVarh` | `Leading_Reactive_Power_kVarh` | Yes |
| `CO2(tCO2)` | `CO2` | Yes |
| `Lagging_Current_Power_Factor` | `Lagging_Power_Factor` | Yes |
| `Leading_Current_Power_Factor` | `Leading_Power_Factor` | Yes |
| `NSM` | `NSM` | Yes |
| `WeekStatus` | `WeekStatus` | Yes (label-encoded) |
| `Day_of_week` | `Day_of_week` | Yes (label-encoded) |
| `Load_Type` | `Load_Type` | Yes (label-encoded) |
| `date` | — | **No** — dropped before modelling |
| `Usage_kWh` | — | Target variable (regression label), not a feature |

### 4.2 Model artifact (`analyst_model.pkl`)

A pickled dictionary:

| Key | Contents |
|---|---|
| `model` | Fitted `XGBRegressor` |
| `feature_columns` | Ordered list of feature column names the model expects at inference time |
| `feature_encoders` | `dict[str, LabelEncoder]` — one fitted encoder per categorical feature |
| `mse` / `r2` | Hold-out test metrics from the most recent training run |

### 4.3 Data retention

`asst` is **stateless with respect to requests** — it retains nothing about a processed image or record after responding, except:

- The persisted model artifact on disk (`analyst_model_path`), which survives restarts and is only replaced by a subsequent `GET /api/train` call.
- Temporary image files, which exist only for the duration of a single `POST /api/image` request and are always deleted by the end of it (success or failure of the downstream forward).

## 5. External interfaces

### 5.1 Inbound API — `http://localhost:8002`

| Method & Path | Purpose | Request | Response |
|---|---|---|---|
| `POST /api/image` | Run defect detection on an uploaded image and forward a positive result to `monitor`. | `multipart/form-data`, field `file` | `{"status": "normal", "file": str}` (no detection) or `{"saved_as": str, "classes": [str]}` (detection) |
| `POST /api/record` | Predict `Usage_kWh` for a sensor record and forward it to `monitor`. | JSON record (see `SPEC_SYSTEM_OVERVIEW.md` §3.2) | `{"status": "ok", "Usage_kWh": float}` |
| `GET /api/train` | (Re)train the `Usage_kWh` regression model. | — | `{"status": "success", "mse": float, "r2": float, "model_path": str}` |

### 5.2 Outbound calls (`asst` → `monitor`)

| Call | Target | Trigger |
|---|---|---|
| `POST /api/image` | `monitor_image_url` (default `http://localhost:8003/api/image`) | FR-A1, only on a qualifying detection |
| `POST /api/record` | `monitor_record_url` (default `http://localhost:8003/api/record`) | FR-A2, on every processed record |

## 6. Configuration reference

| Setting | Default | Description |
|---|---|---|
| `image_in_dir` | `asst/data/img_in` | Temp storage for incoming images |
| `image_out_dir` | `asst/data/img_out` | Temp storage for annotated detection results |
| `monitor_image_url` | `http://localhost:8003/api/image` | Target endpoint for forwarding detected defect images |
| `hf_model_repo_id` | `steven0226/steel-defect-segmentation` | Hugging Face Hub model repository |
| `hf_model_filename` | `steel_defect_yolo26s_seg_best.pt` | Model weights file within the repo |
| `yolo_confidence_threshold` | `0.6` | Minimum detection confidence |
| `training_csv_path` | `asst/data/train/Steel_industry_data.csv` | Dataset used by `GET /api/train` |
| `analyst_model_path` | `asst/data/model/analyst_model.pkl` | Persisted model artifact location |
| `monitor_record_url` | `http://localhost:8003/api/record` | Target endpoint for forwarding predicted records |
| `host` / `port` | `0.0.0.0` / `8002` | Bind address |

## 7. Non-functional requirements

| ID | Requirement |
|---|---|
| A-NFR-1 | `asst` is stateless per request — no image or record is retained after its response is sent, other than the persisted model artifact. |
| A-NFR-2 | The YOLO model is loaded once at process startup (via the FastAPI lifespan hook) and reused across all requests; it is not reloaded per request. |
| A-NFR-3 | The energy-prediction model artifact is re-read from disk on every `POST /api/record`, so a retrain takes effect immediately without restarting the service. |
| A-NFR-4 | All file paths are relative to the process working directory — the service must be started from the repository root. |

## 8. Dependencies & assumptions

- Requires **outbound internet access on first startup** to download YOLO weights from Hugging Face Hub (cached locally by the `huggingface_hub` client afterward; no internet is required for subsequent starts once cached).
- `POST /api/record` depends on a model artifact already existing at `analyst_model_path` — an operator/maintainer must call `GET /api/train` at least once after a fresh checkout or after the training dataset changes.
- Depends on `monitor` being reachable at `monitor_image_url` / `monitor_record_url` to complete forwarding; if `monitor` is unreachable, the forward call raises an error which propagates as a failed response to the caller (`prod_line`), which in turn marks that reading `Failed` (see `SPEC_PROD_LINE.md` FR-P3).
- Assumes live categorical values are a subset of those present in the training dataset (see `SPEC_SYSTEM_OVERVIEW.md` §5).

## 9. Directory layout

```
asst/
├── config.py                  Settings (see §6)
├── main.py                    FastAPI app; loads YOLO model at startup (lifespan)
├── routers/
│   └── api.py                  All 3 endpoints (§5.1)
├── services/
│   ├── image_service.py        Bytes⇄PIL image conversion, temp file save/cleanup
│   ├── yolo_service.py         YOLO model load + inference (FR-A1)
│   └── analyst_service.py      Feature prep, train_model / predict_one (FR-A2, FR-A3)
└── data/
    ├── img_in/                  Transient — uploaded image awaiting inference
    ├── img_out/                 Transient — annotated result awaiting forward
    ├── train/                    Training dataset
    └── model/                    Persisted model artifact
```
