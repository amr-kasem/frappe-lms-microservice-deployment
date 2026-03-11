FROM frappe/bench:latest

# Switch to root for setup
USER root

# Clone Frappe LMS at build time (app at repo root).
RUN git clone --depth 1 -b main https://github.com/frappe/lms.git /workspace/lms

# Copy scripts
COPY microservice-deployment/test/init-backend.sh /workspace/init-backend.sh
COPY microservice-deployment/test/entrypoint.sh /workspace/entrypoint.sh
RUN chmod +x /workspace/init-backend.sh /workspace/entrypoint.sh

ENTRYPOINT ["/workspace/entrypoint.sh"]
