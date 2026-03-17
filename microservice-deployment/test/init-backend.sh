#!/bin/bash
set -e

export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"

SITE_NAME="lms.test"

# Check if bench is fully initialised (not just partially)
if [ -f "/home/frappe/frappe-bench/sites/common_site_config.json" ] && \
   [ -d "/home/frappe/frappe-bench/apps/frappe" ] && \
   [ -d "/home/frappe/frappe-bench/sites/lms.test" ]; then
    echo "Bench already exists, starting..."
    cd frappe-bench
    bench start
    exit 0
fi

# Clean up any partial install (can't rm the mountpoint itself)
rm -rf /home/frappe/frappe-bench/*

echo "=== Configuring bench ==="
# Bench was pre-initialised and apps were installed at image build time.
# Copy the pre-built bench from the image into the volume (only on first run).
if [ ! -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Populating volume from image..."
    cp -a /home/frappe/frappe-bench-image/. /home/frappe/frappe-bench/
fi

cd frappe-bench

# Point to container services
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Remove redis, watch from Procfile (handled by containers)
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

# Ensure gateway-auth is in apps.txt (--skip-assets can omit it)
if ! grep -q frappe_gateway_auth sites/apps.txt; then
    sed -i -e '$a\' sites/apps.txt
    echo "frappe_gateway_auth" >> sites/apps.txt
fi

# Create site
bench new-site "$SITE_NAME" \
    --force \
    --mariadb-root-password 123 \
    --admin-password admin \
    --no-mariadb-socket

bench --site "$SITE_NAME" install-app lms
bench --site "$SITE_NAME" install-app frappe_gateway_auth
bench --site "$SITE_NAME" install-app payments
bench --site "$SITE_NAME" install-app health

# Ensure installed_apps is in site_config (newer Frappe may not write it automatically)
bench --site "$SITE_NAME" set-config installed_apps '["frappe","lms","frappe_gateway_auth","payments","health"]' --parse-json

# Configure site for gateway auth
bench --site "$SITE_NAME" set-config ignore_csrf 1
bench --site "$SITE_NAME" set-config developer_mode 1

# Seed Gateway Auth Settings via console
bench --site "$SITE_NAME" execute frappe.client.set_value \
    --args '["Gateway Auth Settings", "Gateway Auth Settings", "userprofile_url", "http://userprofile:8000/userprofile"]'

bench --site "$SITE_NAME" execute frappe.client.set_value \
    --args '["Gateway Auth Settings", "Gateway Auth Settings", "user_id_header", "X-User-Id"]'

# Seed role mapping: admin → Moderator, student → LMS Student, instructor → Course Creator
bench --site "$SITE_NAME" console <<'PYTHON'
import frappe
frappe.connect(site="lms.test")
settings = frappe.get_single("Gateway Auth Settings")
settings.append("role_mapping", {"external_role": "admin", "frappe_role": "Moderator"})
settings.append("role_mapping", {"external_role": "student", "frappe_role": "LMS Student"})
settings.append("role_mapping", {"external_role": "instructor", "frappe_role": "Course Creator"})
settings.save(ignore_permissions=True)
frappe.db.commit()
print("Role mapping configured:")
for row in settings.role_mapping:
    print(f"  {row.external_role} → {row.frappe_role}")
PYTHON

bench --site "$SITE_NAME" clear-cache
bench use "$SITE_NAME"

echo "=== Backend ready ==="
bench start
