# Microservice deployment (testing)

How to run the LMS stack for **testing** using Docker Compose: backend (Frappe + LMS), standalone frontend, mock userprofile service, MariaDB, Redis, and nginx as gateway.

---

## Required project directory structure

From the **repository root**, the following must exist for **building**:

```
<repo-root>/
├── frappe-lms-separate-frontend/
│   └── frontend/                 # Standalone frontend SPA
│       ├── package.json
│       ├── yarn.lock
│       ├── frontend.Dockerfile
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

- **Backend** is built from repo root; **Frappe LMS** (https://github.com/frappe/lms) is cloned during build.
- **Frontend** is built from repo root using `frappe-lms-separate-frontend/frontend/frontend.Dockerfile`.
- You do **not** need the LMS app on disk; it is cloned from GitHub at image build time.

---

## Steps to deploy (testing)

1. **Prerequisites**
   - Docker and Docker Compose installed.
   - Clone or open the repo so the structure above exists at your workspace root (frontend + microservice-deployment/test).

2. **Run from repository root**
   ```bash
   cd /path/to/<repo-root>
   docker compose -f microservice-deployment/test/docker-compose.yml up -d --build
   ```

3. **First run**
   - Backend performs `bench init`, installs `payments`, `lms`, `frappe_gateway_auth`, creates site `lms.test`, and configures gateway-auth. This can take several minutes (backend healthcheck has a long start period).
   - Check progress: `docker compose -f microservice-deployment/test/docker-compose.yml logs -f backend`

4. **Access**
   - **Gateway (nginx):** http://localhost:8080  
   - **Frontend:** http://localhost:8080/services/lms/frontend/  
   - **Backend API:** http://localhost:8080/services/lms/backend/  
   - Root `/` redirects to `/services/lms/frontend/`.

5. **Stop**
   ```bash
   docker compose -f microservice-deployment/test/docker-compose.yml down
   ```
   Data in `mariadb-data` and `bench-data` volumes is kept. Add `-v` to remove volumes.

---

## Test config summary

- **Site:** `lms.test` (admin password: `admin`).
- **MariaDB root password:** `123`.
- **Gateway auth:** Mock userprofile at `http://userprofile:8000`; nginx injects `X-User-Id: test-user-uuid-001` on backend requests.
- **Frontend** reads `config.json` (mounted from `test/config.json`) for API base URL, app base path, and socket.io URL.
# frappe-lms-microservice-deployment
