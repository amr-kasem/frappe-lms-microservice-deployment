# Testing Phase — Docker Compose Integration Test

## Overview

Validates Phase 1 (gateway auth), Phase 2 (frontend decoupling), and Phase 3
(role sync webhook) end-to-end using a local Docker Compose stack that
simulates the production k3s topology.

No real gateway is needed — nginx injects static mocked user headers, simulating
what the API gateway does in production.

---

## Architecture

```
docker compose up
  │
  ├── nginx (port 8080)
  │     ├── /services/lms/frontend/*  → frontend container (port 80)
  │     ├── /services/lms/backend/*   → backend container (port 8000)
  │     │     strips /services/lms/backend prefix, prepends /api/ before forwarding
  │     └── injects X-User-Id header on all proxied requests to backend
  │
  ├── frontend (nginx serving Vite standalone build)
  │     └── serves /config.json pointing to http://localhost:8080/services/lms/backend
  │
  ├── backend (Frappe + LMS + frappe-gateway-auth)
  │     └── trusts X-User-Id header, provisions users via /userprofile
  │
  └── userprofile (FastAPI mock)
        └── GET /userprofile/{uuid} → returns consistent mocked user data
```

---

## Services

### 1. nginx (API Gateway Simulator)

- Listens on port `8080`
- Routes:
  - `/services/lms/frontend/*` → `frontend:80` (strip prefix)
  - `/services/lms/backend/*` → `backend:8000` (strip prefix, prepend `/api/`)
- Injects headers on all backend-bound requests:
  - `X-User-Id: test-user-uuid-001`
- Does NOT inject headers on frontend-bound requests (frontend is static)

### 2. frontend

- Vite standalone build (`LMS_STANDALONE=1`)
- Serves built bundle via nginx
- `/config.json` mounted via volume:
  ```json
  {
    "api_base_url": "http://localhost:8080/services/lms/backend",
    "app_base_path": "/services/lms/frontend/",
    "socketio_url": "/services/lms/socket.io"
  }
  ```

### 3. backend

- Frappe bench with LMS + frappe-gateway-auth installed
- Site config: `ignore_csrf: 1`
- Gateway Auth Settings configured:
  - `userprofile_url`: `http://userprofile:8000/userprofile`
  - `user_id_header`: `X-User-Id`
  - Role mapping: `admin → Moderator`, `student → LMS Student`

### 4. userprofile (FastAPI Mock)

- `GET /userprofile/{uuid}` returns:
  ```json
  {
    "email": "testuser@example.com",
    "full_name": "Test User",
    "first_name": "Test",
    "last_name": "User",
    "roles": ["admin", "student"]
  }
  ```
- UUID `test-user-uuid-001` returns the above
- Any other UUID returns a different user (deterministic from UUID)
- Unknown format returns 404

---

## Mocked User Contract

The nginx-injected `X-User-Id` and the userprofile response must be consistent:

| Concern | Value |
|---|---|
| X-User-Id header | `test-user-uuid-001` |
| /userprofile response email | `testuser@example.com` |
| /userprofile response roles | `["admin", "student"]` |
| Frappe mapped roles | `Moderator`, `LMS Student` |

---

## Test Cases

### T1 — First Request: JIT User Provisioning
1. Open browser to `http://localhost:8080/services/lms/frontend/`
2. nginx injects `X-User-Id: test-user-uuid-001` on backend requests
3. Frappe auth hook reads header, user not found, calls userprofile mock
4. Shadow user created: `testuser@example.com`, username=`test-user-uuid-001`
5. Roles assigned: `Moderator`, `LMS Student`

**Verify:** Page loads, user name shows "Test User", role-restricted UI visible.

### T2 — Second Request: Existing User
1. Reload the page
2. Auth hook finds existing user by username, skips /userprofile call

**Verify:** Page loads faster (no provisioning), same user context.

### T3 — Frontend Config Loading
1. Frontend fetches `/config.json` from its own nginx
2. Then fetches `{api_base_url}/api/method/lms.lms.api.get_boot`

**Verify:** No Jinja errors, boot data loads, base path correct.

### T4 — API Calls Route Through Gateway
1. Frontend makes `createResource()` calls
2. Custom fetcher prepends `api_base_url`
3. Requests go through nginx gateway to Frappe

**Verify:** Course listing, settings, branding all load correctly.

### T5 — Role Sync Webhook
1. POST to `http://localhost:8080/services/lms/backend/method/frappe_gateway_auth.api.sync_user_roles`
   with `{"user_id": "test-user-uuid-001"}`
2. Frappe re-fetches /userprofile, syncs roles

**Verify:** Roles unchanged (same mock data). Modify mock to return different
roles and re-test to verify diff-based sync.

### T6 — Health Check Bypass
1. `curl http://localhost:8080/services/lms/backend/method/health.api.ping`
   (without X-User-Id header manually — but nginx adds it anyway)

**Verify:** Returns `{"message": "pong"}`.

### T7 — SPA Routing
1. Navigate directly to `http://localhost:8080/services/lms/frontend/courses`
2. nginx serves `index.html` via try_files fallback
3. Vue Router handles the route client-side

**Verify:** Page renders correctly, no 404.

---

## File Structure

```
microservice-deployment/test/
├── docker-compose.yml
├── nginx.conf
├── backend.Dockerfile
├── userprofile/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
└── config.json
```

> Note: `frontend.Dockerfile` is not in this directory — it lives at
> `frappe-lms-separate-frontend/frontend/frontend.Dockerfile`.

---

## Usage

```bash
cd microservice-deployment/test
docker compose up --build
# Open http://localhost:8080/services/lms/frontend/
```

---

## Default Test Credentials

| Identity | Value |
|----------|-------|
| Default injected user (nginx) | `X-User-Id: test-user-uuid-001` |
| Frappe admin password | `admin` |
| MariaDB root password | `123` |
| Frappe site | `lms.test` |

Switch active user via query param: `http://localhost:8080/services/lms/frontend/?user_id=seeder-student-uuid-005`

---

## Definition of Done (Testing Phase)

- [ ] All 4 containers start and are healthy
- [ ] T1: JIT provisioning creates user on first request
- [ ] T2: Subsequent requests skip provisioning
- [ ] T3: Frontend loads boot data via API
- [ ] T4: All API calls route through gateway correctly
- [ ] T5: Role sync webhook works
- [ ] T6: Health check responds without auth
- [ ] T7: SPA deep links work
