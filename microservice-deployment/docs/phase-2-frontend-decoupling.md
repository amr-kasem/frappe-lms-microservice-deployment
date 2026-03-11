# Phase 2 — Frontend Decoupling: Implementation Plan

## Overview

Decouple the Vue frontend from Frappe's page rendering so it can be served from
a standalone nginx container. Frappe becomes a pure API server. The frontend
fetches all boot data via API instead of Jinja injection.

---

## Current Coupling Points

These are the specific places where the frontend depends on being served by Frappe:

| Coupling | Where | What it does |
|---|---|---|
| **Jinja boot data** | `vite.config.js` → `jinjaBootData: true` | Injects `window.csrf_token`, `window.site_name`, `window.lms_path` into HTML at render time via `_lms.py` |
| **SSR HTML template** | `_lms.html` + `_lms.py` | Renders meta tags, title, favicon server-side for SEO |
| **Relative API URLs** | `frappeRequest` (frappe-ui) | All `createResource()` calls go to `/api/method/...` on current origin |
| **Cookie session** | `stores/session.js` | Reads `user_id` cookie to detect logged-in state |
| **Socket.io config** | `socket.js` | Imports `socketio_port` from `common_site_config.json` at build time |
| **Base path** | `utils/basePath.js` | Reads `window.lms_path` (from Jinja boot) |
| **Login redirect** | `stores/user.js` | Redirects to `/login` (Frappe's login page) on AuthenticationError |
| **Logout** | `stores/session.js` | Calls `/logout` (Frappe endpoint) |

---

## Step 1 — Boot API Endpoint

**Goal:** Replace Jinja-injected boot data with a single API call.

**File:** `lms/lms/api.py` (add new whitelisted method)

**Endpoint:** `GET /api/method/lms.lms.api.get_boot`

**Returns:**
```json
{
  "site_name": "mysite.local",
  "lms_path": "lms",
  "frappe_version": "15.x.x",
  "app_name": "Frappe Learning",
  "favicon": "/assets/lms/frontend/favicon.png"
}
```

This consolidates what `_lms.py:get_boot()` and `_lms.py:get_context()` currently inject.

**CSRF token is excluded** — it is disabled via `ignore_csrf: 1` in site config
(Phase 1 prerequisite). The frontend never needs to send one.

**Auth:** This endpoint must work with gateway auth (Phase 1). The gateway injects
`X-User-Id`, Frappe resolves the user, and the boot response is user-aware.

---

## Step 2 — Runtime Config (`/config.json`)

**Goal:** Frontend knows the backend API URL without baking it into the build.

**File:** `/config.json` served by the frontend nginx container (not part of Vite build).

```json
{
  "api_base_url": "https://gateway.example.com/services/lms/api",
  "app_base_path": "/services/lms/app/",
  "socketio_url": ""
}
```

| Field | Purpose |
|---|---|
| `api_base_url` | Absolute URL prefix for all Frappe API calls |
| `app_base_path` | Vue Router history base (e.g. `/services/lms/app/`) |
| `socketio_url` | Socket.io endpoint (empty string = disabled) |

**Injected at deploy time** via k8s ConfigMap → mounted into the nginx container.
Same built image works for all environments by swapping the ConfigMap.

---

## Step 3 — Frontend Config Loader

**Goal:** Load `/config.json` and `get_boot` before mounting the Vue app.

**New file:** `frontend/src/config.js`

```
async loadConfig()
  ├── fetch /config.json → { api_base_url, app_base_path, socketio_url }
  ├── fetch {api_base_url}/api/method/lms.lms.api.get_boot → { site_name, lms_path, ... }
  ├── set window.site_name, window.lms_path from boot response
  └── return merged config object
```

**Called from `main.js` before `createApp()`** — the Vue app does not mount until
config is loaded. This replaces the Jinja injection entirely.

---

## Step 4 — Custom Resource Fetcher

**Goal:** Route all `createResource()` calls to the backend via `api_base_url`.

Currently:
- `setConfig('resourceFetcher', frappeRequest)` uses the default `frappeRequest`
- `frappeRequest` sends `POST /api/method/{dotted.path}` to current origin
- Includes `X-Frappe-CSRF-Token` header from `window.csrf_token`

**Change:** Create a custom fetcher wrapping `frappeRequest` that:
1. Prepends `api_base_url` to the URL
2. Skips CSRF token injection (not needed with gateway auth)
3. Includes credentials mode for cross-origin if needed

**File:** `frontend/src/request.js`

This is the single point where all API traffic is routed. No other file needs
to know about the backend URL.

---

## Step 5 — Session Store Changes

**Goal:** Remove cookie-based session detection.

Currently `session.js`:
```javascript
let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
let _sessionUser = cookies.get('user_id')
```

**With gateway auth:** There is no `user_id` cookie. The user is always authenticated
by the gateway — if the request reaches the frontend, the user is logged in.

**Change:**
- Session detection calls `get_user_info` API instead of reading cookies
- If the API returns a user → logged in
- If it returns `AuthenticationError` → not logged in (shouldn't happen behind gateway, but handle gracefully)
- Remove `/login` redirect (auth is gateway's responsibility, not the frontend's)
- Remove `/logout` resource call (logout is managed by the gateway/parent app)

---

## Step 6 — Socket.io Decoupling

**Goal:** Remove build-time dependency on `common_site_config.json`.

Currently `socket.js`:
```javascript
import { socketio_port } from '../../../../sites/common_site_config.json'
```

This import path only works inside a Frappe bench directory structure.

**Change:**
- Read `socketio_url` from runtime config (`/config.json`)
- If empty/absent → disable socket entirely (acceptable for initial deployment)
- If provided → connect to that URL

Socket.io is used for real-time notifications. In a k3s microservice setup,
this is a separate concern that can be addressed later. **Disabling it for
Phase 2 is acceptable.**

---

## Step 7 — Vite Config Changes

**Goal:** Build a standalone SPA, not a Frappe-served Jinja template.

Current `vite.config.js` uses:
```javascript
frappeui({
    frappeProxy: true,       // ← dev proxy to Frappe backend
    jinjaBootData: true,     // ← Jinja injection of window globals
    buildConfig: {
        indexHtmlPath: '../lms/www/_lms.html',  // ← writes to Frappe's www/
    },
})
```

**Changes:**
- Set `jinjaBootData: false` — boot data comes from API
- Remove `buildConfig.indexHtmlPath` — output stays in `dist/`, not Frappe's www
- Keep `frappeProxy: true` for local dev (proxy to local Frappe instance)
- Add `base` option from environment or default to `/services/lms/app/`
- Output is a plain SPA bundle (`dist/`) ready for nginx

---

## Step 8 — Standalone HTML Entry

**Goal:** Replace the Jinja-templated `index.html` with a plain HTML file.

Current `frontend/index.html` uses Jinja variables: `{{ title }}`, `{{ meta.* }}`,
`{{ favicon }}`.

**Change:** Create a standalone `index.html` with static defaults:
- Static title (e.g. "Learning") — can be updated via JS after boot API loads
- No Jinja variables
- No `_lms.html` output — the build produces a normal SPA bundle

**SEO concern:** SSR meta tags are lost. In the microservice deployment, SEO is
handled by the gateway or a dedicated prerender service — not Frappe's _lms.py.
This is an acceptable tradeoff for Phase 2.

---

## Step 9 — Nginx Container Config

**Goal:** Serve the built frontend as a static SPA.

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Runtime config injected via ConfigMap
    location = /config.json {
        alias /etc/lms/config.json;
    }

    # SPA fallback — all routes go to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Dockerfile** builds the Vite bundle and copies to nginx:
```dockerfile
FROM node:20 AS build
WORKDIR /app
COPY frontend/ .
RUN npm ci && npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

`/config.json` is mounted at deploy time, not baked into the image.

---

## Files Modified (LMS repo — AGPL)

| File | Change | Nature |
|---|---|---|
| `lms/lms/api.py` | Add `get_boot()` endpoint | New code (minimal) |
| `frontend/src/main.js` | Load config before mounting, use custom fetcher | Modified |
| `frontend/src/config.js` | **New** — config loader | New file |
| `frontend/src/request.js` | **New** — custom resource fetcher | New file |
| `frontend/src/stores/session.js` | Remove cookie detection, use API | Modified |
| `frontend/src/stores/user.js` | Remove `/login` redirect | Modified |
| `frontend/src/socket.js` | Read from config, support disabled state | Modified |
| `frontend/src/utils/basePath.js` | Fall back to config value | Modified |
| `frontend/vite.config.js` | Disable Jinja, set base path | Modified |
| `frontend/index.html` | Remove Jinja variables | Modified |

**Note:** All changes are in the LMS repo (AGPL). Keep modifications minimal
and generic. The `frappe-gateway-auth` repo is untouched in this phase.

---

## What Is NOT Changed

- `_lms.py` is **not deleted** — it still works for standard Frappe deployments.
  The decoupled frontend is an alternative deployment mode, not a replacement.
- No backend API signatures change — `createResource()` URLs remain the same
  dotted paths (e.g. `lms.lms.api.get_user_info`).
- Frappe's session management is untouched — gateway auth (Phase 1) handles it.

---

## Testing Plan

### Local Dev Test (no gateway)

**Setup:** Run Frappe locally. Serve frontend from `npm run dev` on a different port.
Set `ignore_csrf: 1` in site config. Create a local `/config.json` pointing to
the Frappe origin.

**Test 1 — Config loads:**
Frontend fetches `/config.json` and then `get_boot` from Frappe.
Verify: App mounts, base path is correct, no Jinja errors.

**Test 2 — User context:**
API calls resolve user correctly via gateway auth (or manual header injection).
Verify: User store populated, role-restricted UI correct.

**Test 3 — Navigation:**
All Vue Router routes work under the configured base path.
Verify: Deep links work, browser back/forward works, no 404s.

**Test 4 — API calls:**
All `createResource()` calls route to the Frappe backend via `api_base_url`.
Verify: Course listing, enrollment, batch access all work.

**Test 5 — No hardcoded URLs:**
Grep the build output for hardcoded origins or localhost references.
Verify: Clean build with only relative asset paths and config-driven API URLs.

### Container Test

**Setup:** Build frontend Docker image. Run alongside Frappe container.
Mount `/config.json` via volume with correct `api_base_url`.

**Test 6 — SPA routing:**
Access any deep URL directly (e.g. `/services/lms/app/courses/my-course`).
Verify: nginx serves `index.html`, Vue Router handles the route.

**Test 7 — Config swap:**
Change `api_base_url` in the ConfigMap, restart nginx.
Verify: Frontend points to new backend without rebuilding.

---

## Definition of Done (Phase 2)

- [ ] `get_boot` API endpoint exists and returns all necessary boot data
- [ ] Frontend loads config from `/config.json` before mounting
- [ ] All API calls route through custom fetcher with configurable base URL
- [ ] No Jinja variables in the HTML template
- [ ] No build-time dependency on Frappe bench directory structure
- [ ] Session detection works without cookies (API-based)
- [ ] Socket.io gracefully disabled when URL not configured
- [ ] Vite build produces a standalone SPA bundle in `dist/`
- [ ] Frontend works when served from a different origin than Frappe
- [ ] Same built image works for multiple environments via config swap
- [ ] Standard Frappe deployment mode (`_lms.py`) still works (not broken)
