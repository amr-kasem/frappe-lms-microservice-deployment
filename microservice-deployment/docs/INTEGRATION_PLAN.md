# LMS Microservice Integration Plan

## Context

Adapting Frappe LMS for deployment in a k3s microservice environment where:

- Auth is managed at the API gateway level — gateway injects `x-user-id` (UUID) headers into every request
- Full user profile is available via an internal `/userprofile` endpoint
- Role sync is orchestrated via a Temporal saga that triggers webhooks into Frappe
- Frontend is served from a separate nginx container to support loose MFE embedding (iframe)
- All traffic to Frappe is guaranteed to go through the gateway (header spoofing is not possible)
- One Frappe instance per tenant
- Base path: `/services/lms/` (gateway handles path stripping before forwarding to Frappe)

## AGPL Boundary

Frappe Framework and Frappe LMS are AGPL-3.0. All custom integration code runs inside a
separate Frappe app (`frappe-gateway-auth`) which is the only artifact that must be open-sourced.

`frappe-gateway-auth` lives in its own public repository — not inside this repo — for three reasons:
- AGPL boundary is a repo boundary: no risk of proprietary logic leaking into the shared artifact
- Independent versioning against Frappe/LMS versions, decoupled from internal release cycles
- Generic enough for any Frappe app behind a gateway, not LMS-specific — community reusable and a clean handoff if Frappe maintainers ever adopt it upstream

It is referenced in deployment as an external pip dependency (installed from git), same as Frappe and LMS themselves.

| Must share (AGPL) | Keep private |
|---|---|
| `frappe-gateway-auth` repo | Temporal saga workflows |
| Any LMS core modifications (target: zero) | API gateway configuration |
| Frontend modifications (target: minimal) | `/userprofile` service |
| | All other microservices |

---

## Phase 1 — Gateway Auth & JIT Provisioning

### Goal
Frappe stops managing authentication. Every request is authenticated by the gateway.
Frappe trusts the injected `x-user-id` header and maintains shadow user records for
referential integrity (`doc.owner`, permission queries, etc.).

### Scope
- Create `frappe-gateway-auth` as a separate public Frappe app (standalone repo)
- Implement `auth_hook` that:
  - Reads `x-user-id` (UUID) from request headers
  - Looks up Frappe `User` by `username = uuid`
  - On miss: calls `/userprofile`, creates shadow `User` (Website User type, email as name, UUID as username), assigns mapped roles
  - Sets `frappe.session.user` synthetically — no real Frappe session created
- Disable CSRF (gateway is the trust boundary, no direct browser-to-Frappe traffic)
- Add role mapping config to LMS Settings: child table of `external_role → frappe_lms_role`
- Frappe LMS roles in scope: `Moderator`, `Course Creator`, `Batch Evaluator`, `LMS Student`

> Detailed implementation plan: [docs/phase-1-gateway-auth.md](docs/phase-1-gateway-auth.md)

### Test Gate
Hit Frappe directly with a manually set `x-user-id` header (no real gateway).
Verify:
- Shadow user created on first request with correct email and full name
- Roles assigned correctly per mapping config
- Subsequent requests skip `/userprofile` call (user already exists)
- `frappe.session.user` resolves correctly in API responses
- Requests without `x-user-id` are rejected

---

## Phase 2 — Frontend Decoupling

### Goal
Frontend is served independently from Frappe. Frappe becomes a pure API server.

### Scope
- Expose `GET /api/method/lms.lms.api.get_boot` endpoint (replaces `_lms.py` boot injection)
  - Returns: `site_name`, `lms_path`, `frappe_version`, user info, branding, sidebar settings
- Add runtime config: `/config.json` served by frontend nginx
  - Contains: `api_base_url`, `app_base_path`
  - Frontend reads this before mounting Vue app (no values baked into build)
- Configure Vite: `base: '/services/lms/app/'`
- Configure Vue Router: `createWebHistory('/services/lms/app/')`
- Frontend nginx container serves built bundle
- Remove dependency on `_lms.py` for any runtime data

> Detailed implementation plan: [docs/phase-2-frontend-decoupling.md](docs/phase-2-frontend-decoupling.md)

### Test Gate
Serve frontend from a separate origin (e.g. `localhost:8080`) pointing at Frappe on a different port.
Verify:
- Boot data loads via API call
- User info resolves correctly
- Full app navigation works
- Role-restricted UI elements behave correctly
- No hardcoded URLs or paths in the build

---

## Phase 3 — Role Sync Webhook

### Goal
When a user's roles change in the upstream identity system, Frappe reflects the change
without requiring re-provisioning or restart.

### Scope
- Add webhook receiver endpoint to `frappe-gateway-auth`:
  - `POST /api/method/frappe_gateway_auth.api.sync_user_roles`
  - Accepts: `{ "user_id": "<uuid>" }`
  - Re-fetches `/userprofile` for that UUID
  - Diffs current `Has Role` records against new roles from profile
  - Applies adds/removes atomically
  - Endpoint is internal-only (gateway enforces access)
- Temporal saga wires to this endpoint on upstream role change event

### Test Gate
Manually POST to the webhook endpoint with a known user UUID.
Verify:
- Roles updated correctly in Frappe `Has Role` records
- Removed roles are dropped, new roles are added
- Unchanged roles are not touched
- User's other data (email, full name) is not modified
- Invalid or unknown UUID returns a clear error

---

## Phase 4 — Gateway & k3s Integration

### Goal
Full end-to-end deployment in the k3s cluster with real gateway routing.

### Scope
- API gateway routing rules:
  - `/services/lms/app/*` → frontend nginx container
  - `/services/lms/api/*` → Frappe container (strip `/services/lms/api` prefix)
- Gateway injects `x-user-id` on all routes to Frappe
- Webhook endpoint for role sync is internal-only (not exposed externally)
- Smoke test full user journey in cluster

### Test Gate
Full user journey through the real gateway:
- Gateway injects `x-user-id` header
- LMS frontend loads from nginx container
- Boot API call succeeds
- User context is correct (name, roles, permissions)
- Enrollment, course access, role-restricted content all behave correctly
- Role sync webhook triggered via Temporal updates roles live without redeployment
