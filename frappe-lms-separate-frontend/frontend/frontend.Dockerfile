FROM node:20-alpine AS build

WORKDIR /app

# Native build deps for npm packages that compile C/C++ addons
RUN apk add --no-cache python3 make g++

# Copy package files and install dependencies
COPY frappe-lms-separate-frontend/frontend/package.json frappe-lms-separate-frontend/frontend/yarn.lock ./
RUN yarn install

# Copy frontend source
COPY frappe-lms-separate-frontend/frontend/ .

# Build standalone SPA
RUN npx vite build

# ─── Production: serve with nginx ──────────────────────────────
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# SPA fallback config
RUN cat > /etc/nginx/conf.d/default.conf <<'NGINX'
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.standalone.html;

    # Runtime config injected via volume mount
    location = /config.json {
        alias /etc/lms/config.json;
    }

    # SPA fallback — all routes serve index.standalone.html
    location / {
        try_files $uri $uri/ /index.standalone.html;
    }
}
NGINX

EXPOSE 80
