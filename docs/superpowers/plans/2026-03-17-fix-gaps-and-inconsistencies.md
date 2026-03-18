# Fix Gaps and Inconsistencies Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all identified gaps and inconsistencies across docs, Docker Compose config, and init scripts so that the test stack and documentation are fully aligned.

**Architecture:** All changes are config/docs fixes — no new code introduced. Each task is self-contained and targets one file or one category of issue.

**Tech Stack:** nginx, Docker Compose, bash (init-backend.sh), Markdown docs

---

## Files to Modify

| File | Changes |
|------|---------|
| `microservice-deployment/docs/phase-testing.md` | Fix stale paths (`/api/` → `/backend/`, `/app/` → `/frontend/`), fix double `/api/` in T5/T6, fix config.json example, add credentials note |
| `microservice-deployment/test/docker-compose.yml` | Add frontend healthcheck; change nginx depends_on to `service_healthy` |
| `microservice-deployment/test/init-backend.sh` | Fix `installed_apps` order to match install order |

---

## Task 1: Fix stale paths and config example in phase-testing.md

**Files:**
- Modify: `microservice-deployment/docs/phase-testing.md`

- [ ] **Step 1: Fix Architecture section — wrong route paths (lines 20–21)**

In the ASCII diagram, replace:
```
  │     ├── /services/lms/app/*  → frontend container (port 80)
  │     ├── /services/lms/api/*  → backend container (port 8000)
  │     │     strips /services/lms/api prefix before forwarding
```
With:
```
  │     ├── /services/lms/frontend/*  → frontend container (port 80)
  │     ├── /services/lms/backend/*   → backend container (port 8000)
  │     │     strips /services/lms/backend prefix, prepends /api/ before forwarding
```

- [ ] **Step 1b: Fix Architecture section — stale frontend config comment (line 26)**

Replace:
```
  │     └── serves /config.json pointing to http://nginx:8080/services/lms/api
```
With:
```
  │     └── serves /config.json pointing to http://localhost:8080/services/lms/backend
```

Note: `nginx:8080` was wrong — `api_base_url` is loaded by the browser, so it uses `localhost`.

- [ ] **Step 2: Fix nginx service routes in Services section (lines 43–44)**

Replace:
```
  - `/services/lms/app/*` → `frontend:80` (strip prefix)
  - `/services/lms/api/*` → `backend:8000` (strip prefix)
```
With:
```
  - `/services/lms/frontend/*` → `frontend:80` (strip prefix)
  - `/services/lms/backend/*` → `backend:8000` (strip prefix, prepend `/api/`)
```

- [ ] **Step 3: Fix frontend config.json example (lines 55–59)**

Replace:
```json
  ```json
  {
    "api_base_url": "http://localhost:8080/services/lms/api",
    "app_base_path": "/services/lms/app/",
    "socketio_url": ""
  }
  ```
```
With:
```json
  ```json
  {
    "api_base_url": "http://localhost:8080/services/lms/backend",
    "app_base_path": "/services/lms/frontend/",
    "socketio_url": "/services/lms/socket.io"
  }
  ```
```

- [ ] **Step 4: Fix T1 URL reference (line 105)**

Replace:
```
1. Open browser to `http://localhost:8080/services/lms/app/`
```
With:
```
1. Open browser to `http://localhost:8080/services/lms/frontend/`
```

- [ ] **Step 5: Fix broken URL in T5 (line 133)**

Replace:
```
1. POST to `http://localhost:8080/services/lms/api/api/method/frappe_gateway_auth.api.sync_user_roles`
```
With:
```
1. POST to `http://localhost:8080/services/lms/backend/method/frappe_gateway_auth.api.sync_user_roles`
```

Note: nginx rewrite is `^/services/lms/backend/(.*) /api/$1` — it prepends `/api/` to whatever follows `/backend/`. So the caller writes `/backend/method/...` and the backend receives `/api/method/...`. Including `/api/` in the caller URL would double it to `/api/api/method/...`.

- [ ] **Step 6: Fix broken URL in T6 (line 141)**

Replace:
```
1. `curl http://localhost:8080/services/lms/api/api/method/health.api.ping`
```
With:
```
1. `curl http://localhost:8080/services/lms/backend/method/health.api.ping`
```

- [ ] **Step 7: Fix T7 SPA URL (line 147)**

Replace:
```
1. Navigate directly to `http://localhost:8080/services/lms/app/courses`
```
With:
```
1. Navigate directly to `http://localhost:8080/services/lms/frontend/courses`
```

- [ ] **Step 8: Fix Usage section URL (line 177)**

Replace:
```
# Open http://localhost:8080/services/lms/app/
```
With:
```
# Open http://localhost:8080/services/lms/frontend/
```

- [ ] **Step 9: Add default credentials note**

Add a new section after `## Usage`:
```markdown
## Default Test Credentials

| Identity | Value |
|----------|-------|
| Default injected user (nginx) | `X-User-Id: test-user-uuid-001` |
| Frappe admin password | `admin` |
| MariaDB root password | `123` |
| Frappe site | `lms.test` |

Switch active user via query param: `http://localhost:8080/services/lms/frontend/?user_id=seeder-student-uuid-005`
```

- [ ] **Step 10: Commit**

```bash
git add microservice-deployment/docs/phase-testing.md
git commit -m "docs: fix stale path names and double /api/ errors in phase-testing.md"
```

---

## Task 2: Add frontend healthcheck and tighten nginx dependency

**Files:**
- Modify: `microservice-deployment/test/docker-compose.yml`

**Context:** The frontend service currently has no healthcheck, so nginx depends on it with only `service_started` — it starts forwarding before the nginx inside the frontend container is ready. Adding an HTTP healthcheck makes the dependency deterministic.

- [ ] **Step 1: Add healthcheck to frontend service**

In `docker-compose.yml`, after the `frontend` service's `volumes:` block, add:
```yaml
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost/"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 30s
```

`wget` is available in the nginx:alpine image used by the frontend. We use port 80 (the internal nginx port inside the frontend container).

- [ ] **Step 2: Change nginx depends_on frontend from `service_started` to `service_healthy`**

In `docker-compose.yml`, the `nginx` service `depends_on` block, change:
```yaml
      frontend:
        condition: service_started
```
To:
```yaml
      frontend:
        condition: service_healthy
```

- [ ] **Step 3: Commit**

```bash
git add microservice-deployment/test/docker-compose.yml
git commit -m "fix: add frontend healthcheck and tighten nginx depends_on to service_healthy"
```

---

## Task 3: Fix installed_apps order in init-backend.sh

**Files:**
- Modify: `microservice-deployment/test/init-backend.sh`

**Context:** Line 60 sets `installed_apps` to `["frappe","payments","lms","frappe_gateway_auth","health"]` but the apps are installed in order `lms → frappe_gateway_auth → payments → health`. The config should reflect actual install order in case Frappe resolves hooks/patches by position.

- [ ] **Step 1: Fix the installed_apps array order (line 60)**

Replace:
```bash
bench --site "$SITE_NAME" set-config installed_apps '["frappe","payments","lms","frappe_gateway_auth","health"]' --parse-json
```
With:
```bash
bench --site "$SITE_NAME" set-config installed_apps '["frappe","lms","frappe_gateway_auth","payments","health"]' --parse-json
```

- [ ] **Step 2: Commit**

```bash
git add microservice-deployment/test/init-backend.sh
git commit -m "fix: align installed_apps order with actual install sequence in init-backend.sh"
```

---

## Task 4: Document seeder timeout risk in phase-testing.md

> **Must follow Task 1** — both tasks modify the same file; Task 1 must be committed first.

**Files:**
- Modify: `microservice-deployment/docs/phase-testing.md`

**Context:** The seeder retries for `30 × 5s = 150s`. The backend `start_period` is `300s`. On a slow first boot (cold Docker pull, slow mariadb init), the seeder can time out before the backend is healthy. This needs to be documented as a known limitation.

- [ ] **Step 1: Add known limitations section to phase-testing.md**

Add the following text before the `## Definition of Done` section (insert it as a new Markdown section; no nested code fences needed):

Section title: `## Known Limitations`

Sub-heading: `### Seeder timeout on first cold boot`

Body text:
> The seeder polls the backend for up to 150 seconds (30 retries × 5s). The backend's `start_period` allows up to 300 seconds before health check failures are counted. On a slow first boot (cold image pull, slow MariaDB init), the seeder may time out before the backend is ready.

Workaround note:
> **Workaround:** Re-run the seeder manually after the backend becomes healthy:

Workaround command block (bash):
```
docker compose run --rm seeder
```

- [ ] **Step 2: Commit**

```bash
git add microservice-deployment/docs/phase-testing.md
git commit -m "docs: document seeder timeout limitation on slow first boot"
```

---

## Verification

After all tasks, verify:

- [ ] `phase-testing.md` has no remaining references to `/services/lms/api/` or `/services/lms/app/`

  ```bash
  grep -n "lms/api\|lms/app" microservice-deployment/docs/phase-testing.md
  # Expected: no output
  ```

- [ ] `docker-compose.yml` frontend service has a healthcheck and nginx uses `service_healthy`

  ```bash
  grep -A6 "frontend:" microservice-deployment/test/docker-compose.yml | grep -E "healthcheck|service_healthy"
  ```

- [ ] `installed_apps` order matches install order

  ```bash
  grep "installed_apps\|install-app" microservice-deployment/test/init-backend.sh
  # lms, frappe_gateway_auth, payments, health — same in both
  ```
