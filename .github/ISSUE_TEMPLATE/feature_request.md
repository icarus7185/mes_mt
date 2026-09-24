---
name: AI-Native Feature Request
about: Standard template enforcing UI/Data/API split and AI constraints
title: '[FEAT]: '
labels: 'enhancement, pending-dor'
---

### 1. Business Intent & Scope
- **Problem Statement:**
- **In Scope:**
- **Out of Scope (Non-Goals):**

### 2. Architectural Decomposition
- **UI Layer:** (Screens, input fields, validation rules, error states)
- **Data Layer:** (Entities, schema changes, constraints, PII classification)
- **API Layer:** (REST endpoints, HTTP verbs, payload specs, status codes, authz)

### 3. AI Copilot Execution Constraints
- **Target Tech Stack:** Python 3.11 / FastAPI / Pydantic v2 / PostgreSQL
- **Allowed Directory Scope:** `src/modules/work_orders/`, `tests/unit/`
- **Dependency Guardrail:** Do NOT introduce external third-party dependencies without architectural review.

### 4. Acceptance Criteria (Gherkin-lite)
- [ ] **Given** an authenticated user, **When** submitting valid WO payload, **Then** return HTTP 201 Created.
- [ ] **Given** invalid PII inputs, **When** submitting, **Then** return HTTP 422 with field-level validation errors.

### 5. Definition of Ready (DoR) Checklist
- [ ] UI/Data/API split strictly defined.
- [ ] Non-goals explicitly declared.
- [ ] PII & Security classification stated.
