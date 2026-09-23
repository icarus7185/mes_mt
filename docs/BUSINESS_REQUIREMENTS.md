# Business Requirements Document (BRD)

## MES Monitoring System — Steel Surface Defect Detection & Energy Usage Prediction

| | |
|---|---|
| **Document type** | Business Requirements Document (overview level) |
| **Companion documents** | `docs/SPEC_SYSTEM_OVERVIEW.md`, `docs/SPEC_PROD_LINE.md`, `docs/SPEC_ASST.md`, `docs/SPEC_MONITOR.md` — detailed technical specifications |
| **Project / Repository** | `mes_mt` |
| **Version** | 1.0 |
| **Date** | 2026-09-23 |
| **Status** | Approved for baseline (reverse-documented) |
| **Prepared by** | Business Analyst (AI-assisted) |
| **Prepared for** | Project sponsor / stakeholders |

### Revision history

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0 | 2026-09-23 | Business Analyst | Initial baseline, capturing the business intent behind the existing system. |

> **How to read this document.** This BRD describes the system at a **business level** — the problem it solves, who it's for, and what it lets them do — without implementation detail. For exact technical behavior (API contracts, data schemas, configuration values, code-level business rules), see the companion technical specs: `docs/SPEC_SYSTEM_OVERVIEW.md` (cross-service architecture & data flow) and the per-service specs `docs/SPEC_PROD_LINE.md`, `docs/SPEC_ASST.md`, `docs/SPEC_MONITOR.md`.

---

## 1. Executive summary

The customer operates a steel production line and wants better visibility into two things that are currently hard to see in real time: **surface quality** (are defects slipping through?) and **energy behavior** (is the line consuming power the way it should?).

This system is a proof-of-concept monitoring platform that watches the line, uses AI to interpret what it sees and predict energy usage, and puts both on a single live dashboard an operator can glance at throughout a shift — without needing a data analyst, a database administrator, or a heavyweight MES rollout to get value from it.

Because a live camera and live plant sensors were not available for this proof-of-concept, the system **simulates** both feeds from representative sample data, so the customer can evaluate the concept end-to-end before committing to hardware integration.

## 2. Business background & problem statement

| Pain point today | What the customer wants instead |
|---|---|
| Surface defects on steel sheets are typically caught by manual/spot inspection, which is inconsistent and easy to miss under time pressure. | Continuous, automated visual inspection that flags defects the moment they occur, with the evidence image kept for review. |
| Energy consumption is usually only understood after the fact (utility bill, monthly report), so abnormal usage goes unnoticed until it's already expensive. | A live, predictive view of energy draw, so unusual consumption is visible the same shift it happens, not the next billing cycle. |
| Plant networks and data links are not always perfectly reliable; when a reading fails to reach the monitoring system, operators often don't know it happened at all. | Every reading is accounted for — if it couldn't be sent, the dashboard says so explicitly, instead of silently going missing. |
| Monitoring tools are often expensive, slow to deploy, and require dedicated infrastructure/IT support before anyone sees value. | A lightweight system that a small team can stand up quickly, understand end-to-end, and demonstrate value from on day one. |

## 3. Business objectives

1. **Catch surface defects automatically**, reducing reliance on manual visual inspection and shrinking the time between a defect occurring and someone knowing about it.
2. **Predict energy usage in near real time**, so unusual consumption patterns are visible to operators as they happen, not discovered later in a bill or report.
3. **Make data reliability visible**, so operators can trust that "no alert" means "nothing happened" rather than "the message got lost."
4. **Keep the solution simple and self-contained**, so it can be demonstrated, evaluated, and iterated on quickly without a large infrastructure investment.
5. **Present everything in one place**, on a dashboard that a shift operator — not a data scientist — can read at a glance.

## 4. Stakeholders and their needs

| Stakeholder | What they need from this system |
|---|---|
| **Shift operator (primary user)** | A single screen showing the latest defect alerts and the current energy trend, in plain language, refreshed automatically. |
| **Production/line engineer** | A way to verify, while commissioning or troubleshooting, that the simulated line is producing and sending readings correctly, and to see when something fails to send. |
| **Plant/process manager** | Confidence that energy usage is being watched continuously, and a historical trail of predictions they can review later. |
| **Quality manager** | An accessible archive of recent detected defects (with the evidence image) to support quality reviews and root-cause discussions. |
| **Data science / ML owner** | The ability to retrain the energy-prediction model when better or more recent data becomes available. |
| **Project sponsor** | A working, demonstrable proof of concept that clearly shows the business value before further investment in real hardware integration. |

## 5. Scope overview (business level)

### 5.1 In scope

- **Automated visual defect detection** on steel surface images, using AI to identify defects and keep a visual record of the ones found.
- **Predictive energy monitoring**, using AI to estimate power consumption for each incoming sensor reading and chart it over time.
- **A live operations dashboard** showing current defect alerts, a rolling history of recent alerts, current and trending energy usage, and key at-a-glance indicators (average usage, trend direction, data freshness, how much of the recent load has been "heavy").
- **A line-side view** for engineers to see, in real time, what the (simulated) line is capturing and whether each reading successfully made it downstream.
- **Simulated unreliable transmission**, so the customer can see how the system behaves — and what it looks like on-screen — when readings fail to arrive, before this is tested against a real, imperfect plant network.
- **A permanent, reviewable log** of every energy prediction made, for later analysis.

### 5.2 Out of scope (for this phase)

- Connecting to a real camera or real plant sensors/PLC/SCADA system (this phase uses representative sample data to simulate both feeds).
- Automated alerting outside the dashboard (email, SMS, chat notifications) when a defect or anomaly is detected.
- Multi-user accounts, permissions, or login/security hardening.
- Running the system across multiple sites, multiple lines, or at production scale (this is a single-line, single-instance proof of concept).
- Long-term image storage for every defect ever found (the dashboard's image archive intentionally keeps only the most recent ones; only the energy-prediction log is kept in full).

## 6. Key capabilities (what the customer gets)

1. **See defects as they happen.** Every captured image is automatically inspected; only genuine detections are surfaced, each with a visual, zoomable record of what was found and when.
2. **See energy trends, not just numbers.** Predicted energy usage is shown both as a live-updating chart and as headline figures (current average, trend vs. the last reading, how much of the recent activity was heavy load) — so a trend is obvious without reading a table.
3. **Know when something didn't get through.** Every simulated transmission — successful or not — is shown on screen with a clear status, so gaps in the data are visible rather than invisible.
4. **Know when the pipeline goes quiet.** The dashboard actively tracks how long it's been since the last new reading arrived and calls it out visually if that gap grows too large — an early warning that something upstream may have stopped.
5. **Review recent history at a glance.** Both the defect-alert gallery and the energy-reading grid keep a rolling window of recent activity, always visible without digging through logs or files.
6. **Keep a durable record for later analysis.** Every energy prediction is permanently logged to a file the business can open, export, or analyze later, independent of what's currently on screen.
7. **Retrain the model as data improves.** The energy-prediction model can be refreshed on demand as more or better historical data becomes available, without redeploying the system.

## 7. Success criteria

| Goal | How success is observed |
|---|---|
| Defects are caught automatically | Genuine surface defects appear as alerts on the dashboard, with a usable evidence image, without manual triggering. |
| Energy behavior is visible in near real time | The energy chart and headline figures update continuously and reflect the latest readings within a few seconds. |
| Transmission failures are never silent | Every reading shown anywhere in the system is clearly marked as sent successfully or not. |
| The system is easy to demonstrate and reason about | All three parts of the system (line simulator, AI worker, dashboard) can be started independently and observed end-to-end by a non-developer stakeholder. |
| The concept can evolve toward the real plant | The simulated camera/sensor feeds can be swapped for real ones later without redesigning the dashboard or the AI logic. |

## 8. Assumptions & business constraints

- This is a **proof-of-concept / demonstration phase**; hardware integration (real camera, real sensors) is a future phase, not part of this deliverable.
- The sample data used to simulate the line (sample images, a historical energy dataset) is **representative** of real production conditions, but not a guarantee of real-world model accuracy — the model should be retrained on real plant data before any production decision relies on it.
- The system is sized for **evaluation and demonstration**, not for running unattended, at scale, or with multiple concurrent lines.
- No dedicated IT/operations team is assumed to be available to run the system — it is intentionally simple to start and observe.

## 9. High-level risks

| Risk | Business impact if unaddressed |
|---|---|
| The energy-prediction model is only as good as the historical data it was trained on. | Predictions may be inaccurate if real plant behavior differs materially from the training data; the model should be revalidated before being trusted for cost decisions. |
| The proof-of-concept has no user access control. | Not suitable to expose beyond a trusted internal demonstration audience as-is. |
| Simulated data stands in for real camera/sensor feeds. | Business value shown today is indicative, not a guarantee of results once connected to the real line; a follow-up validation phase against live data is recommended. |
| No automated alerting beyond the dashboard. | Findings are only actionable if someone is actively watching the screen; a future phase should consider push notifications for critical events. |

## 10. Next steps (recommended)

1. Stakeholder review and sign-off on this business intent against the delivered proof of concept.
2. Plan a follow-up phase to connect a real camera feed and real plant sensors in place of the simulated data sources.
3. Define who is accountable for periodically retraining the energy-prediction model as real data accumulates.
4. Decide whether/when authentication, alerting, and multi-line scaling become requirements for a production rollout.

---

*For the detailed technical requirements, API contracts, data schemas, and configuration reference behind every capability described above, see `docs/SPEC_SYSTEM_OVERVIEW.md` and the per-service specs `docs/SPEC_PROD_LINE.md`, `docs/SPEC_ASST.md`, `docs/SPEC_MONITOR.md`.*
