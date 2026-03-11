# Project Status

## Overview

This project adapts Frappe LMS for deployment in a microservice environment where
authentication is handled by an API gateway, the frontend is served independently
from Frappe, and the entire stack runs in k3s.

---

## Repository Structure

All work lives under `mcait-lms/`:

```
mcait-lms/
├── lms/                              # Upstream Frappe LMS — untouched
├── frappe-gateway-auth/              # Gateway auth Frappe app — complete
├── frappe-lms-separate-frontend/     # Standalone Vue SPA — complete
│   └── frontend/
├── microservice-deployment/          # Docker Compose test stack — complete
│   └── test/
└── docs/                             # Planning and status docs
```

---

## Path Contract

All paths are fixed and consistent across all components:

| Service | Path |
|---|---|
| Frontend | `/services/lms/frontend/` |
| Backend (Frappe API) | `/services/lms/backend/` |
| Socket.IO | `/services/lms/socket.io/` |

---

## Component Status

### 1. `lms/` — Upstream Frappe LMS

**Status: Untouched — used as-is**

- Fresh clone of upstream Frappe LMS
- Zero modifications
- Installed into Frappe bench via `bench get-app /workspace/lms/lms`
- All original functionality preserved

---

### 2. `frappe-gateway-auth/` — Gateway Auth App

**Status: Complete**

A separate public Frappe app (AGPL) that handles all gateway integration at the
Frappe layer. Installed from git: `https://github.com/amr-kasem/frappe-gateway-auth.git`

**What it does:**
- Auth hook reads `X-User-Id` header (UUID) injected by the API gateway
- JIT user provisioning: on first request, calls internal `/userprofile` endpoint,
  creates a Frappe shadow user (email + UUID as username), assigns mapped roles
- Subsequent requests skip provisioning (user already exists)
- Disables CSRF (`ignore_csrf: 1`) — gateway is the trust boundary
- Role sync webhook: `POST /api/method/frappe_gateway_auth.api.sync_user_roles`
  — re-fetches `/userprofile` for a given UUID and diffs/applies role changes

**Configuration (set in Frappe site config / Gateway Auth Settings):**
- `userprofile_url`: internal URL of the userprofile service
- `user_id_header`: header name (default `X-User-Id`)
- Role mapping table: `external_role → Frappe LMS role`

**Role mappings (test environment):**

| External Role | Frappe LMS Role |
|---|---|
| `admin` | `Moderator` |
| `student` | `LMS Student` |
| `instructor` | `Course Creator` |

---

### 3. `frappe-lms-separate-frontend/` — Standalone Frontend

**Status: Complete**

A standalone Vue SPA derived from the upstream Frappe LMS frontend, fully decoupled
from Frappe's Jinja rendering engine. Served by its own nginx container.

**Key changes from upstream:**

| File | Change |
|---|---|
| `vite.config.js` | Standalone-only: `base: '/services/lms/frontend/'`, `jinjaBootData: false`, `frappeProxy: false` |
| `src/config.js` | Fetches `config.json` via `import.meta.env.BASE_URL + 'config.json'` before app mounts |
| `src/main.js` | Always uses gateway fetcher; no telemetry; no dual-mode logic |
| `src/request.js` | Always prepends `api_base_url` to all API calls |
| `src/utils/call.js` | Same as request.js for direct `call()` usage |
| `src/stores/session.js` | No cookie detection; `isLoggedIn` purely from `userResource.data` |
| `src/stores/user.js` | No `/login` redirect on `AuthenticationError` |
| `src/router.js` | Always awaits `userResource.promise`; never redirects to `/login` |
| `src/socket.js` | Config-driven URL only; no `common_site_config` dependency |
| `src/utils/basePath.js` | Reads `config.app_base_path`; defaults to `services/lms/frontend` |
| `index.html` | Deleted (Jinja template) |
| `index.standalone.html` | Static HTML entry point (no Jinja variables) |
| `package.json` | Build script simplified to `vite build` |
| `frontend.Dockerfile` | Multi-stage node→nginx build; COPY paths relative to `mcait-lms/` root |

**Removed from 7 component files:**
- All `window.location.href = '/login'` redirects (gateway handles auth)
- "Log in" menu entries in `MobileLayout.vue` and `UserDropdown.vue`
- Login button in `NoPermission.vue` (replaced with "Checkout Courses" link)
- Auth guard redirects in `BatchForm.vue`, `AssignmentSubmission.vue`, `Programs.vue`
- Permission redirect in `LessonForm.vue` (replaced with `router.push({ name: 'Courses' })`)

**Runtime config (`/services/lms/frontend/config.json`):**
```json
{
  "api_base_url": "https://gateway.example.com/services/lms/backend",
  "app_base_path": "/services/lms/frontend/",
  "socketio_url": ""
}
```
Mounted at deploy time via k8s ConfigMap or Docker volume. Same built image works
for all environments by swapping config only.

**Known non-critical:**
- `window.read_only_mode` is never set in standalone mode (always `undefined` = falsy).
  All edit/create controls are visible to users with Frappe permission. This is correct
  default behavior. To use read-only mode, expose `frappe.flags.read_only` via a
  settings API endpoint and populate it from config.

---

### 4. `microservice-deployment/test/` — Docker Compose Test Stack

**Status: Complete**

Simulates the full production topology locally. No real API gateway needed.

**Architecture:**
```
nginx (:8080)  ← gateway simulator
├── /services/lms/frontend/* → frontend container (:80)  [prefix stripped]
└── /services/lms/backend/*  → backend container (:8000) [prefix stripped, X-User-Id injected]

frontend       ← nginx serving Vite SPA + config.json
backend        ← Frappe bench (LMS + frappe-gateway-auth)
userprofile    ← FastAPI mock returning test user data
mariadb        ← database
redis          ← cache / queue
```

**Files:**

| File | Purpose |
|---|---|
| `docker-compose.yml` | Orchestrates all 6 services |
| `nginx.conf` | Gateway simulator: routing, prefix stripping, X-User-Id injection |
| `config.json` | Frontend runtime config (volume-mounted into frontend container) |
| `backend.Dockerfile` | Frappe bench image; build context is `mcait-lms/` root |
| `entrypoint.sh` | Fixes volume ownership, drops to `frappe` user |
| `init-backend.sh` | Full bench init: installs apps, creates site, seeds config and role mappings |
| `userprofile/` | FastAPI mock with 3 test users |

**Build context:** All Dockerfiles use `context: ../../` (= `mcait-lms/`). Paths
in Dockerfiles are relative to `mcait-lms/`:
- Backend scripts: `microservice-deployment/test/`
- Frontend source: `frappe-lms-separate-frontend/frontend/`
- LMS app (mounted): `/workspace/lms/lms`

**Test users (from mock userprofile service):**

| UUID | Email | Roles |
|---|---|---|
| `test-user-uuid-001` | testuser@example.com | admin, student → Moderator, LMS Student |
| `test-user-uuid-002` | instructor@example.com | instructor → Course Creator |
| `test-user-uuid-003` | student@example.com | student → LMS Student |

Gateway nginx injects `X-User-Id: test-user-uuid-001` on all backend requests.

**To run:**
```bash
cd mcait-lms/microservice-deployment/test
docker compose up --build
# Open http://localhost:8080/services/lms/frontend/
```

---

## What Is NOT Done

### Phase 4 — k3s Deployment
Real cluster deployment with:
- Actual API gateway (not nginx mock)
- k8s manifests / Helm chart (see `lms-infra/` repo)
- ConfigMap for `config.json`
- Role sync wired to Temporal saga

### `window.read_only_mode`
Not exposed via config or API in standalone mode. Functional LMS works without it
(all controls visible to permitted users). Address only if read-only mode is required.

### SEO / Prerendering
`_lms.py` SSR meta tags are not used in standalone mode. SEO requires a dedicated
prerender service at the gateway level.

---

## AGPL Boundary

| Repository | License | Must be public |
|---|---|---|
| `lms/` (upstream) | AGPL-3.0 | Yes (upstream) |
| `frappe-gateway-auth/` | AGPL-3.0 | Yes (separate repo) |
| `frappe-lms-separate-frontend/` | AGPL-3.0 | Yes (derived from AGPL frontend) |
| `microservice-deployment/` | Private | No |
| k3s/infra config | Private | No |
| Temporal workflows | Private | No |
