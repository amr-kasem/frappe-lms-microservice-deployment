FROM frappe/bench:latest

# Switch to root for setup
USER root

# Clone all GitHub apps at build time as root (network: host is reliable here).
RUN for i in 1 2 3; do \
      git clone --depth 1 -b main https://github.com/frappe/lms.git /workspace/lms && break \
      || (echo "lms clone attempt $i failed, retrying..." && rm -rf /workspace/lms && sleep 5); \
    done \
 && for i in 1 2 3; do \
      git clone --depth 1 https://github.com/frappe/payments.git /workspace/payments && break \
      || (echo "payments clone attempt $i failed, retrying..." && rm -rf /workspace/payments && sleep 5); \
    done \
 && for i in 1 2 3; do \
      git clone --depth 1 https://github.com/amr-kasem/frappe-gateway-auth.git /workspace/frappe-gateway-auth && break \
      || (echo "frappe-gateway-auth clone attempt $i failed, retrying..." && rm -rf /workspace/frappe-gateway-auth && sleep 5); \
    done

# Copy scripts and health app
COPY microservice-deployment/test/init-backend.sh /workspace/init-backend.sh
COPY microservice-deployment/test/entrypoint.sh /workspace/entrypoint.sh
COPY microservice-deployment/test/health /workspace/health
RUN chmod +x /workspace/init-backend.sh /workspace/entrypoint.sh

# Hand off all cloned apps to frappe so git doesn't reject dubious ownership.
RUN chown -R frappe:frappe /workspace/lms /workspace/health /workspace/payments /workspace/frappe-gateway-auth

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
 && bench get-app /workspace/payments \
 && bench get-app /workspace/lms \
 && bench get-app /workspace/health \
 && bench get-app --skip-assets /workspace/frappe-gateway-auth

USER root
ENTRYPOINT ["/workspace/entrypoint.sh"]
