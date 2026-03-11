#!/bin/bash
# Fix volume ownership (runs as root), then drop to frappe user
chown -R frappe:frappe /home/frappe/frappe-bench 2>/dev/null || true

exec su frappe -c "bash /workspace/init-backend.sh"
