# Security & UI/UX Audit Findings

Date: 2026-03-01

## Scope
- Backend (`backend/*.py`)
- Frontend (`frontend/src/**/*`)

---

## High Severity Findings

### 1) Insecure default JWT secret allows token forgery in misconfigured deployments
**Why it matters:** If `JWT_SECRET_KEY` is not set, the app falls back to a hardcoded development secret. Attackers can mint valid JWTs and impersonate users/roles.

**Evidence:** `backend/app.py` sets `JWT_SECRET_KEY` to `dev-secret-key-change-in-production` when env var is missing.

**Recommendation:**
- Fail fast at startup when `JWT_SECRET_KEY` is missing/weak.
- Enforce minimum entropy/length requirements for secrets.

---

### 2) Privilege escalation via open registration roles (admin, super_admin, recruiter, etc.)
**Why it matters:** Public registration accepts privileged roles, enabling unauthorized users to self-register as high-privilege accounts.

**Evidence:** `VALID_ROLES` in `backend/auth.py` includes privileged roles and `/register` trusts client-supplied `role`.

**Recommendation:**
- Restrict self-registration to lowest privilege role(s) only.
- Require admin-only invitation flow for privileged role assignment.

---

### 3) Missing role authorization on question bank endpoints
**Why it matters:** Several question bank endpoints only require authentication, not admin/interviewer authorization checks. Any logged-in user can read/toggle question banks.

**Evidence:** Endpoints `/question-bank/<id>` (GET) and `/question-bank/<id>/toggle` (PATCH) in `backend/admin_routes.py` are decorated with `@jwt_required()` but do not validate role.

**Recommendation:**
- Add centralized RBAC decorators (e.g., `@require_admin_role` / allowed roles) to every sensitive endpoint.
- Add tests verifying non-privileged users receive 403.

---

## Medium Severity Findings

### 4) Detailed exception messages are returned to clients
**Why it matters:** Returning raw exception strings can leak internals (SQL errors, schema details, paths), helping attackers with enumeration and exploit development.

**Evidence:** Multiple routes in `backend/auth.py` and `backend/admin_routes.py` return `str(e)` in JSON responses.

**Recommendation:**
- Return generic error messages externally.
- Log full stack traces server-side with correlation IDs.

---

### 5) Rate limiter exists but is not initialized
**Why it matters:** Authentication and upload endpoints appear unthrottled, increasing brute-force and abuse risk.

**Evidence:** `backend/rate_limiter.py` defines `init_rate_limiting`, but no usage is found across the app.

**Recommendation:**
- Initialize rate limiting in app startup.
- Apply stricter limits on auth, upload, and expensive analysis endpoints.

---

### 6) Client stores JWT in `localStorage` (XSS blast radius)
**Why it matters:** Any successful XSS can read `localStorage` and exfiltrate tokens for account takeover.

**Evidence:** `frontend/src/pages/LoginPage.jsx` writes token to `localStorage`; `frontend/src/services/api.js` reads it for Authorization header.

**Recommendation:**
- Move auth to secure, HttpOnly, SameSite cookies.
- Harden CSP and eliminate inline/eval script allowances.

---

### 7) HTTP API base URLs are defaulted in frontend
**Why it matters:** The frontend constructs `http://` API URLs by default, risking token/session exposure over plaintext transport outside local development.

**Evidence:** `frontend/src/services/api.js` builds `http://localhost:5000` and `http://<hostname>:5000`.

**Recommendation:**
- Prefer relative `/api` paths behind same-origin reverse proxy, or enforce HTTPS-only base URLs.

---

## Low Severity / UI-UX Findings

### 8) Password rule mismatch between frontend and backend
**Why it matters:** Frontend login validation allows 6+ chars while backend registration requires 8+, creating inconsistent user expectations and avoidable friction.

**Evidence:** `frontend/src/pages/LoginPage.jsx` validates `password.length < 6`; backend registration in `backend/auth.py` enforces 8+ chars.

**Recommendation:**
- Centralize validation rules and reuse consistently between frontend/backend.

---

### 9) Login messaging is role-biased and may confuse users
**Why it matters:** Login subtitle says “interviewer dashboard” even though admins/proctors also log in there, causing avoidable confusion.

**Evidence:** Login page copy in `frontend/src/pages/LoginPage.jsx`.

**Recommendation:**
- Use role-neutral text (“your dashboard”) and optionally show destination after auth.

---

## Dependency Audit Attempt
- `npm audit --omit=dev --json` was attempted in `frontend/`.
- The registry audit endpoint returned `403 Forbidden` in this environment, so dependency CVE review could not be completed here.

---

## Suggested Remediation Order
1. Enforce secure JWT secret policy (startup fail-fast).
2. Lock down role assignment in registration and add invitation/admin provisioning flow.
3. Apply RBAC checks to all question bank endpoints.
4. Remove sensitive error leakage.
5. Enable and verify rate limiting.
6. Replace localStorage tokens with HttpOnly cookies + HTTPS-only API transport.
7. Align validation and role-neutral UX copy.
