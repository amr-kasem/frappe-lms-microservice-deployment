# LMS Frontend

Vue 3 SPA for the Learning Management System. Standalone build, runtime config, and a dedicated API gateway so the app can be deployed under any base path and talk to a separate backend.

## Stack

- **Vue 3** (Composition API, `<script setup>`)
- **Vite 5** — build and dev server
- **Vue Router 4** — history-mode routing with base path support
- **Pinia** — state (session, user, settings, sidebar)
- **frappe-ui** — UI primitives, resources, and data patterns
- **Tailwind CSS** — styling
- **TypeScript** — used in selected modules (e.g. `utils/code.ts`, Settings/Coupons types)

## Requirements

- Node 18+
- npm or pnpm

## Setup

```bash
npm install
```

## Scripts

| Command       | Description                    |
|---------------|--------------------------------|
| `npm run dev` | Dev server (Vite, HMR)         |
| `npm run build` | Production build (standalone) |
| `npm run serve` | Preview production build      |

## Project layout

```
src/
├── main.js           # Bootstrap: loadConfig → router, Pinia, FrappeUI, gateway fetcher
├── App.vue
├── router.js        # Route definitions, base path from config
├── config.js        # Runtime config loader (config.json)
├── request.js       # createGatewayFetcher — rewrites API URLs to backend
├── utils/
│   ├── call.js      # Backend RPC (uses api_base_url, no /api/method double prefix)
│   ├── basePath.js
│   └── ...
├── stores/          # Pinia: session, user, settings, sidebar
├── pages/           # Route-level views (Courses, Batches, Lesson, etc.)
└── components/      # Shared UI and feature components
```

## Runtime config

The app expects a **config.json** at the app base (e.g. `/services/lms/frontend/config.json`). It is loaded before the app mounts and is typically provided by the reverse proxy (e.g. nginx) or a ConfigMap in k8s.

| Key             | Purpose                          |
|-----------------|----------------------------------|
| `api_base_url`  | Backend base URL for API calls   |
| `app_base_path` | Public base path (default `/services/lms/frontend/`) |
| `socketio_url`  | Optional Socket.IO endpoint     |

See `src/config.js` for defaults and loading logic.

## API / backend

- **Resources** (frappe-ui `createResource`, `createListResource`, etc.) go through the configured **resourceFetcher**, which is a gateway fetcher that rewrites relative URLs to `api_base_url` (see `request.js`).
- **RPC-style calls** use `@/utils/call`: it builds the full URL from `api_base_url` and `/method/<method>` (or a path you pass), then uses `fetch` so the backend receives requests at the correct path (no double `/api/method/` prefix).

## Build and deployment

- **Base path**: Set in Vite as `base: '/services/lms/frontend/'`. Change it if the app is served under another path.
- **Entry**: Build uses `index.standalone.html` for a self-contained SPA (no backend-rendered shell).
- **PWA**: Optional Vite PWA plugin is configured; adjust `workbox` paths if the build output is deployed to a different directory.

## Conventions

- Use `@/` for `src/` (see Vite `resolve.alias`).
- Prefer Composition API and `<script setup>` for new components.
- i18n: use the `__()` helper from the translation plugin for user-facing strings.
- Backend calls: use `call()` from `@/utils/call` for one-off RPC; use frappe-ui resources for list/doc patterns so they benefit from the gateway fetcher.
