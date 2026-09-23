# Python Coding Rules

## `mes_mt` — Coding Standard for AI-Assisted Review

| | |
|---|---|
| **Document type** | Coding standard / static review checklist |
| **Applies to** | All Python source under `prod_line/`, `asst/`, `monitor/` (and any future Python service in this repository) |
| **Audience** | Human contributors **and** AI coding agents performing a code review or a rule-compliance check |
| **Version** | 1.0 |
| **Date** | 2026-09-23 |
| **Status** | Baseline, derived from the conventions already in use across the three existing services |

---

## 0. How to use this document (read this first if you are an AI agent)

When asked to **"check coding rules"**, **"review against `CODING_RULES.md`"**, or similar:

1. Treat every rule below as an individually checkable item, identified by its **Rule ID** (e.g. `PY-014`).
2. Each rule carries a keyword: **MUST** (a violation is a defect to report), **SHOULD** (a violation is worth flagging but may be justified by a code comment or context), or **MAY** (informational, do not flag as a defect).
3. For each file you review, go rule by rule within the sections that apply to that file's role (see the **Scope** tag on each rule: `all`, `service`, `router`, `config`, `model/ML`, `frontend-py` (Jinja/static-serving code), etc.).
4. Report findings as: `Rule ID — file:line — one-sentence description of the violation`. Do not report a rule as violated if the rule's **Scope** does not apply to that file.
5. If a rule and the actual code disagree but the surrounding code comment or docstring explains a deliberate exception, do not flag it — note it as an accepted exception instead.
6. §13 contains a compact **checklist form** of every MUST rule, intended for fast pass/fail scanning of a diff.

---

## 1. Project & module structure

**Scope: all**

| ID | Rule | Rationale |
|---|---|---|
| PY-001 | Each microservice **MUST** live in its own top-level package (`prod_line/`, `asst/`, `monitor/`) and **MUST NOT** import from another service's package. Cross-service communication happens only over HTTP. | Keeps the services independently deployable, as documented in `docs/SPEC_SYSTEM_OVERVIEW.md`. |
| PY-002 | Within a service package, use the established layout: `config.py` (settings), `main.py` (FastAPI app + lifespan), `routers/` (HTTP endpoints), `services/` (business logic), and, where needed, a module-level state holder (e.g. `state.py`) for in-memory data. | Matches the existing structure of all three services; new contributors and AI agents can predict where code lives. |
| PY-003 | One responsibility per module. A router module **MUST NOT** contain business logic beyond request/response glue — delegate to a `services/` class or function. | Keeps HTTP concerns (validation, status codes) separate from domain logic, which is easier to test and reuse. |
| PY-004 | Every module **SHOULD** open with a short (1–3 line) triple-quoted module docstring describing its purpose — no more. | Matches existing files (e.g. `"""Background loop: every ``settings.interval_seconds``, send a random image..."""`). A long docstring is a sign the module is doing too much. |

## 2. Naming conventions

**Scope: all**

| ID | Rule | Rationale |
|---|---|---|
| PY-010 | Modules, functions, and variables **MUST** use `snake_case`. Classes **MUST** use `PascalCase`. Constants **MUST** use `UPPER_SNAKE_CASE`. | Standard PEP 8; consistently followed today (`ImageService`, `RecordHistoryService`, `DATE_FORMAT`, `COLUMN_RENAMES`). |
| PY-011 | Boolean variables and function names **SHOULD** read as a predicate (`is_`, `has_`, `success`, `enabled`) rather than an ambiguous noun. | Improves readability at call sites (e.g. `success = random.random() >= settings.record_send_failure_rate`). |
| PY-012 | A module-level singleton instance **MUST** be named after its purpose in `snake_case`, not the class name (e.g. `settings = Settings()`, `producer_state = ProducerState()`, `record_service = RecordService(...)`). | Existing, consistent pattern across all three services. |
| PY-013 | Private/internal helper functions **MUST** be prefixed with a single underscore (`_prepare_features`, `_load_artifact`, `_predict_features`). | Signals "not part of the module's public contract" without a formal access-control mechanism. |

## 3. Type hints

**Scope: all**

| ID | Rule | Rationale |
|---|---|---|
| PY-020 | Every function/method signature **MUST** have type hints on all parameters and the return type, including `-> None` where nothing is returned. | Already the norm in every file reviewed; enables static analysis and IDE support. |
| PY-021 | Use modern built-in generics and union syntax (`list[str]`, `dict[str, float]`, `str \| Path`) rather than importing `List`/`Dict`/`Union` from `typing`, unless targeting a Python version that requires it. | Matches current code (`list[str]`, `dict[str, LabelEncoder] \| None`, `str \| Path`). |
| PY-022 | Use `Optional[X]` (or `X \| None`) explicitly for any value that can be `None` — never rely on an untyped default. | Prevents `NoneType has no attribute` bugs; already used (`Optional[Path]`, `Optional[bytes]`). |
| PY-023 | File-system paths **MUST** be typed and constructed as `pathlib.Path`, never as raw strings, except at the point they cross an external boundary (e.g. a CLI argument or an HTTP response). | Consistent with every `config.py` and service in the repo. |

## 4. Imports

**Scope: all**

| ID | Rule | Rationale |
|---|---|---|
| PY-030 | Imports **MUST** be absolute, rooted at the top-level package (`from prod_line.config import settings`), never relative (`from .config import settings`). | Matches every existing import in the codebase; avoids ambiguity when a module is run directly vs. imported. |
| PY-031 | Import order **MUST** follow: (1) standard library, (2) third-party packages, (3) first-party (`prod_line`/`asst`/`monitor`) packages — each group separated by a blank line, alphabetized within the group. | Matches the existing style in every reviewed file (e.g. `asyncio`/`logging` → `httpx` → `prod_line.config`/`prod_line.state`). |
| PY-032 | **MUST NOT** import a submodule only to reach into another service's internals (e.g. reaching into `asst.services.yolo_service` from `monitor`). Only HTTP calls cross a service boundary. | See PY-001; enforces the microservice boundary at the code level, not just by convention. |

## 5. Documentation & comments

**Scope: all**

| ID | Rule | Rationale |
|---|---|---|
| PY-040 | Default to **no inline comments**. Add one only when it explains a non-obvious *why* (a hidden constraint, a workaround, a business rule that isn't derivable from the code itself). | Matches the existing style — e.g. the comment on `DROPPED_COLUMNS` in `analyst_service.py` explaining *why* `date` is excluded, not *what* the line does. |
| PY-041 | **MUST NOT** add a comment that merely restates what the next line of code already says. | Comments that restate code rot and mislead once the code changes; they add no information. |
| PY-042 | A function/method docstring is **SHOULD**, not MUST — add one when the function's behavior has a business rule or edge case that isn't obvious from its name and signature (e.g. "returns `(None, [])` if nothing detected"). Trivial getters/setters **SHOULD NOT** have a docstring. | Matches the existing codebase, which docstrings selectively rather than exhaustively. |
| PY-043 | **MUST NOT** reference a specific past bug fix, ticket number, or "added for X feature" inside a comment or docstring. That context belongs in the commit message / PR description, not in the source. | Such comments rot as the code evolves independently of the history that motivated them. |

## 6. Configuration management

**Scope: config**

| ID | Rule | Rationale |
|---|---|---|
| PY-050 | All tunable values for a service **MUST** live in that service's `config.py`, as fields on a single `pydantic.BaseModel` subclass named `Settings`, instantiated once as `settings = Settings()`. | Existing, consistent pattern; a single source of truth per service. |
| PY-051 | Every `Settings` field **MUST** have a default value and a one-line `#` comment directly above it explaining what it controls. | Matches every existing `config.py`; keeps configuration self-documenting without a separate reference doc. |
| PY-052 | **MUST NOT** read configuration ad hoc from environment variables, files, or hardcoded literals scattered through service/router code — always go through `settings`. | Prevents configuration drift and keeps `config.py` the single place to look. |
| PY-053 | A probability, rate, or threshold setting **MUST** be named to make its unit/range obvious (`*_failure_rate` in `[0, 1]`, `*_threshold`, `*_seconds`). | Matches `image_send_failure_rate`, `yolo_confidence_threshold`, `interval_seconds`. |

## 7. Logging

**Scope: all**

| ID | Rule | Rationale |
|---|---|---|
| PY-060 | Every module that logs **MUST** obtain its logger via `logger = logging.getLogger(__name__)` at module scope — **MUST NOT** call `logging.info(...)` etc. on the root logger directly. | Preserves per-module log source attribution; existing convention everywhere. |
| PY-061 | Log calls **MUST** use `%`-style lazy formatting (`logger.info("Sent %s to asst", filename)`), **MUST NOT** use an f-string or `.format()` inside a log call. | Avoids formatting the string when the log level would discard it; matches every existing log call. |
| PY-062 | An exception caught and handled (not re-raised) **MUST** be logged with `logger.exception(...)` (inside an `except` block) so the traceback is captured, not `logger.error(...)`. | Matches existing pattern in every `except httpx.HTTPError:` block. |
| PY-063 | Each service **MUST** configure logging once, in `main.py`, with both a `FileHandler` under `logs/<service>.log` and a `StreamHandler` (console) — **MUST NOT** configure logging anywhere else. | Matches the existing `logging.basicConfig(...)` block duplicated identically (by design) across the three `main.py` files. |

## 8. Error handling

**Scope: all**

| ID | Rule | Rationale |
|---|---|---|
| PY-070 | A background loop (e.g. a producer loop) **MUST** catch `Exception` around its per-tick body so one failed iteration cannot kill the loop, and **MUST** log via `logger.exception` before continuing. | Matches `producer_loop`/`record_producer_loop`; a core reliability requirement (`P-NFR-1` in `SPEC_PROD_LINE.md`). |
| PY-071 | An outbound HTTP call **MUST** catch `httpx.HTTPError` specifically (not a bare `except Exception`) at the call site that needs to react to a failed send. | Narrow catches avoid silently swallowing unrelated bugs; matches every outbound `client.post(...)` call in the codebase. |
| PY-072 | **MUST NOT** use a bare `except:` anywhere. | Hides `KeyboardInterrupt`/`SystemExit` and masks programming errors; not used anywhere in the current codebase — keep it that way. |
| PY-073 | A function that can meaningfully fail for a caller-fixable reason (e.g. a missing model artifact, a missing required column) **SHOULD** raise a specific, descriptive exception (`FileNotFoundError`, `ValueError`) with a message that names the missing thing, rather than returning a sentinel or failing silently. | Matches `_load_artifact`'s `FileNotFoundError` and `train_model`'s `ValueError` for a missing target column. |

## 9. Async & concurrency

**Scope: service, router**

| ID | Rule | Rationale |
|---|---|---|
| PY-080 | A FastAPI route handler that performs I/O (HTTP call, file read/write) **MUST** be declared `async def` and **MUST** use `await` on the I/O call (e.g. `httpx.AsyncClient`), never a blocking call. | Matches every router in the codebase; blocking calls inside `async def` stall the whole event loop. |
| PY-081 | Shared mutable in-memory state accessed from more than one coroutine (a background loop and a request handler) **MUST** be guarded by an `asyncio.Lock` around both the read and the write path. | Matches `ProducerState`/`RecordHistoryState`'s `async with self._lock:` pattern; prevents torn reads under concurrent access. |
| PY-082 | A long-lived `httpx.AsyncClient` **MUST** be created once (in a lifespan/background-loop scope) and reused, **MUST NOT** be instantiated per request/per tick. | Matches `async with httpx.AsyncClient(...) as client:` wrapping the whole loop, and `app.state.http_client` created once in `lifespan`. |
| PY-083 | A background task started in a FastAPI `lifespan` **MUST** be cancelled in the `finally` block of that same lifespan. | Matches every `main.py`; prevents orphaned tasks on shutdown/reload. |

## 10. FastAPI / API design

**Scope: router**

| ID | Rule | Rationale |
|---|---|---|
| PY-090 | Every router **MUST** be declared with an explicit `APIRouter(prefix="/api")` (or no prefix for a page route) and included in `main.py` via `app.include_router(...)` — routes **MUST NOT** be attached directly to the `FastAPI()` app instance outside of `main.py`. | Matches every service's `routers/api.py` + `routers/dashboard.py` split. |
| PY-091 | A JSON endpoint's return type **SHOULD** be annotated (`-> dict`) and its shape **MUST** be stable and documented in the service's `SPEC_*.md` — changing a response field name is a breaking change and **MUST** be reflected in `docs/SPEC_SYSTEM_OVERVIEW.md` §3 if the field crosses a service boundary. | Keeps the cross-service contract (the JSON payload) and the documentation in sync. |
| PY-092 | An endpoint that can legitimately have "nothing yet" (no image sent yet, no records yet) **MUST** return a well-formed empty/`null` response (`200`), **MUST NOT** return `404` for that case — `404` is reserved for "this specific identified resource does not exist" (e.g. `GET /api/hist/{filename}` for an unknown filename). | Matches the existing contract exactly (see `SPEC_MONITOR.md` §3 FR-M4). |
| PY-093 | A file-serving endpoint that accepts a filename from the URL **MUST** resolve the path and verify it is still inside the intended directory (`path.is_relative_to(root)`) before reading it. | Matches `monitor`'s `GET /api/hist/{filename}` guard; prevents path traversal. |

## 11. Data models (Pydantic / dataclasses)

**Scope: config, service, model/ML**

| ID | Rule | Rationale |
|---|---|---|
| PY-100 | Use `pydantic.BaseModel` for configuration (`Settings`) and for any structure that needs validation. Use `@dataclass` for simple, unvalidated internal state holders (e.g. `LastSent`). **MUST NOT** use a plain untyped `dict` to model a stable, named shape. | Matches `Settings(BaseModel)` vs. `@dataclass class LastSent`. |
| PY-101 | A `dataclass` used as mutable shared state **MUST** give every field a sensible default (`Optional[...] = None`) so an "empty" instance is always constructible. | Matches `LastSent()` being constructible before anything has been sent. |
| PY-102 | Raw external payload dictionaries that cross a service boundary (the JSON record described in `docs/SPEC_SYSTEM_OVERVIEW.md` §3) **MAY** remain plain `dict[str, Any]` at the transport layer, but any code that reads *specific* fields off them **SHOULD** do so with `.get(...)` and a sensible default, never direct indexing, since the schema is external and not enforced by a model class. | Matches `record.get("date")` usage throughout routers. |

## 12. Machine-learning code (`asst/services/analyst_service.py` and similar)

**Scope: model/ML**

| ID | Rule | Rationale |
|---|---|---|
| PY-110 | Feature-engineering logic (column renames, dropped columns, encoding) **MUST** be implemented as a single shared function (e.g. `_prepare_features`) used by both the training path and every prediction path — **MUST NOT** be duplicated between train and predict. | Prevents train/serve skew; matches the existing single `_prepare_features` used by `train_model`, `predict`, and `predict_one`. |
| PY-111 | A column that is not a genuine predictive feature (e.g. a live timestamp never seen during training) **MUST** be explicitly excluded via a named constant (`DROPPED_COLUMNS`) with a comment explaining *why*, not silently handled ad hoc. | Matches the existing `DROPPED_COLUMNS = ["date"]` with its rationale comment; makes the modelling decision auditable. |
| PY-112 | A trained model artifact **MUST** be persisted together with everything needed to reproduce its exact input pipeline at inference time (feature column order, fitted encoders) — **MUST NOT** persist the model alone and re-derive encoders at predict time. | Matches the `analyst_model.pkl` artifact dict (`model`, `feature_columns`, `feature_encoders`); prevents silent train/serve mismatches. |
| PY-113 | A prediction function **MUST** validate that all `feature_columns` the model expects are present in the incoming data and raise a descriptive `ValueError` listing the missing ones, rather than letting the model call fail with an opaque error. | Matches the existing `missing_columns` check in `_predict_features`. |

## 13. Formatting & general style

**Scope: all**

| ID | Rule | Rationale |
|---|---|---|
| PY-120 | Code **MUST** be valid, idiomatic Python 3.10+ (uses `X \| Y` unions, `match` where it clarifies, walrus operator only where it improves clarity). | Matches the `str \| Path` style already in use. |
| PY-121 | Line length **SHOULD** stay under ~110 characters; break long call chains/argument lists across multiple lines rather than relying on line-continuation backslashes. | Matches the multi-line `svgEl(...)`-style call formatting already used for long calls. |
| PY-122 | String formatting for anything user- or log-facing **SHOULD** use f-strings (except inside logging calls — see PY-061). | Matches usage like `f"{stem}_{timestamp}{suffix}"`. |
| PY-123 | A function **SHOULD** do one thing; if a function mixes "decide" and "do" (e.g. compute a value *and* perform I/O *and* mutate shared state), consider splitting it — but do not force a split that only adds indirection without adding clarity. | Judgment-based; balances PY-003's separation-of-concerns goal against over-engineering. |

## 14. Testing

**Scope: all**

| ID | Rule | Rationale |
|---|---|---|
| PY-130 | New business logic in a `services/` module **SHOULD** be accompanied by a unit test when a test suite exists for that service. | No automated test suite exists in this repository at the time of writing (documented as a known limitation in `docs/SPEC_SYSTEM_OVERVIEW.md` §5) — treat this as forward-looking guidance, not a current MUST. |
| PY-131 | Any test that is added **MUST NOT** require a live network call to Hugging Face Hub or to another running service; external calls **MUST** be stubbed/mocked. | Keeps tests fast and runnable offline/in CI. |

## 15. Security baseline

**Scope: all**

| ID | Rule | Rationale |
|---|---|---|
| PY-140 | **MUST NOT** log secrets, credentials, or API keys, even at debug level. (Not currently applicable — the system has no secrets — but binding for any future addition, e.g. a Hugging Face token.) | Standard baseline; nothing in the current codebase violates this. |
| PY-141 | Any endpoint that accepts a filename/path component from the client **MUST** apply the PY-093 containment check before touching the filesystem. | Prevents path traversal; only currently relevant to `GET /api/hist/{filename}`. |
| PY-142 | **MUST NOT** introduce a new third-party dependency without adding it to `requirements.txt` with a pinned version, matching the existing pinning style (`package==x.y.z`). | Matches the existing `requirements.txt`; keeps builds reproducible. |

---

## 16. MUST-rule compliance checklist

Use this table for a fast pass/fail scan of a diff or file. Every row is a `MUST`-level rule from above.

| ID | Check |
|---|---|
| PY-001 | No cross-service imports. |
| PY-002 | Service follows `config.py` / `main.py` / `routers/` / `services/` layout. |
| PY-003 | Router files contain no business logic. |
| PY-010 | Naming case conventions followed. |
| PY-012 | Singleton instances named after purpose, not class. |
| PY-013 | Internal helpers prefixed `_`. |
| PY-020 | All signatures fully type-hinted. |
| PY-023 | Paths are `pathlib.Path`, not raw strings. |
| PY-030 | Imports are absolute, first-party rooted. |
| PY-032 | No reaching into another service's internals. |
| PY-041 | No comments that restate the code. |
| PY-043 | No bug-ticket/feature-name references in comments. |
| PY-050 | All tunables live in `Settings`. |
| PY-051 | Every `Settings` field has a default + comment. |
| PY-052 | No ad hoc config reads outside `settings`. |
| PY-060 | Module-scoped `logger = logging.getLogger(__name__)`. |
| PY-061 | Log calls use `%`-style args, not f-strings. |
| PY-062 | Handled exceptions logged with `logger.exception`. |
| PY-063 | Logging configured only once, in `main.py`. |
| PY-070 | Background loop body wrapped in `try/except Exception`. |
| PY-071 | Outbound HTTP calls catch `httpx.HTTPError` specifically. |
| PY-072 | No bare `except:`. |
| PY-080 | I/O route handlers are `async def` with `await`. |
| PY-081 | Shared mutable state guarded by `asyncio.Lock`. |
| PY-082 | `httpx.AsyncClient` reused, not per-call. |
| PY-083 | Lifespan-started tasks cancelled in `finally`. |
| PY-090 | Routes attached via `APIRouter` + `include_router`, not on the app directly. |
| PY-092 | "Nothing yet" returns `200` with empty/`null`, not `404`. |
| PY-093 | Filename-from-URL endpoints validate path containment. |
| PY-100 | Config uses `BaseModel`; simple state uses `@dataclass`. |
| PY-110 | Feature engineering shared between train/predict paths. |
| PY-112 | Model artifact persists encoders + feature order alongside the model. |
| PY-113 | Prediction validates required feature columns present. |
| PY-131 | Tests never call live external services. |
| PY-140 | No secrets logged. |
| PY-141 | Path-containment check applied to filename-from-URL endpoints. |
| PY-142 | New dependencies pinned in `requirements.txt`. |
