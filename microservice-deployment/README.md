# Microservice Deployment

Docker Compose–based deployment for testing the LMS stack: Frappe backend with [Frappe LMS](https://github.com/frappe/lms), standalone frontend SPA, mock userprofile service, MariaDB, Redis, and nginx as the gateway.

---

## Requirements

- Docker and Docker Compose
- This repository cloned so that `frappe-lms-separate-frontend/` and `microservice-deployment/` exist under the repository root

---

## Repository layout

Build expects the following under the repository root:

```
<repo-root>/
├── frappe-lms-separate-frontend/
│   └── frontend/              # Standalone frontend (Vue/Vite)
│       ├── frontend.Dockerfile
│       ├── package.json
│       └── ...
└── microservice-deployment/
    └── test/
        ├── docker-compose.yml
        ├── backend.Dockerfile
        ├── init-backend.sh
        ├── entrypoint.sh
        ├── nginx.conf
        ├── config.json
        ├── userprofile/
        │   ├── Dockerfile
        │   ├── main.py
        │   └── requirements.txt
        └── ...
```

- **Backend image:** Built from repo root; [Frappe LMS](https://github.com/frappe/lms) is cloned during build. The LMS app is not required on the host.
- **Frontend image:** Built from repo root via `frappe-lms-separate-frontend/frontend/frontend.Dockerfile`.

---

## Deployment

From the repository root:

```bash
docker compose -f microservice-deployment/test/docker-compose.yml up -d --build
```

**First run:** The backend runs `bench init`, installs `payments`, `lms`, and `frappe_gateway_auth`, creates the site `lms.test`, and applies gateway-auth configuration. Allow several minutes; the backend healthcheck uses a long start period. To follow logs:

```bash
docker compose -f microservice-deployment/test/docker-compose.yml logs -f backend
```

**Stop (keep data):**

```bash
docker compose -f microservice-deployment/test/docker-compose.yml down
```

Add `-v` to remove named volumes and delete data.

---

## Endpoints

| Purpose    | URL |
|-----------|-----|
| Gateway   | http://localhost:8080 |
| Frontend  | http://localhost:8080/services/lms/frontend/ |
| Backend API | http://localhost:8080/services/lms/backend/ |

Requests to `/` are redirected to `/services/lms/frontend/`.

---

## Test configuration

| Item | Value |
|------|--------|
| Site | `lms.test` |
| Admin password | `admin` |
| MariaDB root password | `123` |
| Gateway auth | Mock userprofile at `http://userprofile:8000`; nginx adds `X-User-Id: test-user-uuid-001` to backend requests |
| Frontend config | `config.json` (mounted from `test/config.json`): API base URL, app base path, Socket.IO URL |

---

## License

Copyright (C) 2025.

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU Affero General Public License** as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU Affero General Public License](https://www.gnu.org/licenses/agpl-3.0.html) for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
