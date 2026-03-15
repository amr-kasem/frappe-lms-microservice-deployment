FROM frappe/bench:latest

# Switch to root for setup
USER root

# Clone Frappe LMS at build time (app at repo root).
RUN git clone --depth 1 -b main https://github.com/frappe/lms.git /workspace/lms

# Copy scripts
COPY microservice-deployment/test/init-backend.sh /workspace/init-backend.sh
COPY microservice-deployment/test/entrypoint.sh /workspace/entrypoint.sh
RUN chmod +x /workspace/init-backend.sh /workspace/entrypoint.sh

# Hand off lms clone to frappe so git doesn't reject it as dubious ownership.
RUN chown -R frappe:frappe /workspace/lms

# Pre-initialise bench and install all apps at build time (network: host in
# compose build context gives reliable connectivity; avoids runtime internet
# dependency).
USER frappe
ENV PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}" \
    DEBIAN_FRONTEND=noninteractive \
    GIT_TERMINAL_PROMPT=0
RUN for i in 1 2 3; do \
      echo N | bench init --skip-redis-config-generation --ignore-exist /home/frappe/frappe-bench-image && break \
      || (echo "bench init attempt $i failed, retrying..." && rm -rf /home/frappe/frappe-bench-image && sleep 5); \
    done \
 && cd /home/frappe/frappe-bench-image \
 && bench get-app payments \
 && bench get-app /workspace/lms \
 && bench get-app --skip-assets https://github.com/amr-kasem/frappe-gateway-auth.git

USER root
ENTRYPOINT ["/workspace/entrypoint.sh"]
