# LMS — Learning Management System

A full learning management system built around [Frappe LMS](https://github.com/frappe/lms): a **standalone Vue.js frontend** that talks to a **Frappe backend** over an API gateway, with optional **microservice-style deployment** (separate backend, frontend, and gateway auth).

---

## What this repository contains

| Part | Description |
|------|-------------|
| **Standalone frontend** | Vue 3 SPA (Vite, Pinia, Vue Router, frappe-ui, Tailwind). Courses, lessons, batches, certifications, quizzes, assignments, programs, jobs, billing, statistics, profiles. Runtime config and gateway fetcher so it can be served under any base path and use a remote backend. |
| **Microservice deployment** | Docker Compose setup for testing: Frappe bench + Frappe LMS (cloned at build), this frontend, mock userprofile service, MariaDB, Redis, nginx as gateway. Backend uses [frappe-gateway-auth](https://github.com/amr-kasem/frappe-gateway-auth) for external auth. |

The **LMS backend app** (Frappe LMS) is not stored in this repo; the test deployment image clones it from GitHub at build time.

---

## Repository layout

```
<repo-root>/
├── frappe-lms-separate-frontend/
│   ├── frontend/                    # Standalone LMS SPA (Vue 3, Vite)
│   │   ├── src/                     # App code (pages, components, stores, utils)
│   │   ├── frontend.Dockerfile
│   │   └── README.md
│   └── frappe-ui/                   # UI library used by the frontend
├── microservice-deployment/
│   ├── test/                        # Docker Compose test stack
│   │   ├── docker-compose.yml
│   │   ├── backend.Dockerfile       # Frappe + LMS (clone from GitHub)
│   │   ├── frontend.Dockerfile      # Builds frontend image
│   │   ├── init-backend.sh
│   │   ├── nginx.conf
│   │   ├── config.json              # Frontend runtime config
│   │   └── userprofile/             # Mock auth service
│   └── README.md
├── license.txt                      # GNU AGPL v3
└── README.md                        # This file
```

---

## Frontend (standalone SPA)

- **Stack:** Vue 3, Vite 5, Vue Router 4, Pinia, frappe-ui, Tailwind CSS; some TypeScript.
- **Features:** Home, Courses (list/detail/learn/certification), Batches, Lesson viewer (including SCORM), Quizzes, Assignments, Programming exercises, Programs, Jobs, Statistics, Billing, User profiles (about, certificates, roles, evaluator), Data import, Settings (members, categories, badges, coupons, payment gateways, etc.).
- **Config:** Loads `config.json` at app base (e.g. `/services/lms/frontend/config.json`) for `api_base_url`, `app_base_path`, `socketio_url`. All API calls go through a gateway fetcher so the backend can live on another host/path.
- **Docs and scripts:** See [frappe-lms-separate-frontend/frontend/README.md](frappe-lms-separate-frontend/frontend/README.md). From that directory: `npm install`, `npm run dev`, `npm run build`.

---

## Microservice deployment (testing)

Runs the full stack in Docker: MariaDB, Redis, Frappe backend (with LMS and gateway-auth), standalone frontend, mock userprofile service, nginx as single entrypoint.

- **Requirements:** Docker and Docker Compose; repo cloned so `frappe-lms-separate-frontend/` and `microservice-deployment/` exist.
- **Run (from repo root):**
  ```bash
  docker compose -f microservice-deployment/test/docker-compose.yml up -d --build
  ```
- **Access:** Gateway http://localhost:8080; frontend at http://localhost:8080/services/lms/frontend/; backend API at http://localhost:8080/services/lms/backend/.

Full steps, endpoints, and test config are in [microservice-deployment/README.md](microservice-deployment/README.md).

---

## License

Copyright (C) 2025.

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU Affero General Public License** as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU Affero General Public License](https://www.gnu.org/licenses/agpl-3.0.html) for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <https://www.gnu.org/licenses/>. The full license text is in [license.txt](license.txt).
