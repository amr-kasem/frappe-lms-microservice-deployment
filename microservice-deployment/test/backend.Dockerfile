# ── Stage 1: bench init ───────────────────────────────────────────────────────
FROM frappe/bench:latest AS bench-builder

USER frappe
ENV PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}" \
    DEBIAN_FRONTEND=noninteractive \
    GIT_TERMINAL_PROMPT=0

RUN for i in 1 2 3; do \
      echo N | bench init --skip-redis-config-generation --ignore-exist /home/frappe/frappe-bench-image && break \
      || (echo "bench init attempt $i failed, retrying..." && rm -rf /home/frappe/frappe-bench-image && sleep 5); \
    done

# ── Stage 2: install apps via bench get-app (uses remote URLs, not local paths,
#    to avoid the 'App' has no .org bug in this bench version) ─────────────────
RUN cd /home/frappe/frappe-bench-image \
 && bench get-app --skip-assets https://github.com/frappe/payments.git \
 && bench get-app --branch main https://github.com/frappe/lms.git \
 && bench get-app --skip-assets https://github.com/amr-kasem/frappe-gateway-auth.git

# Install the local health app — copy it into apps/ and wire it up manually
# (bench get-app with local paths is broken).
USER root
COPY microservice-deployment/test/health /workspace/health
RUN chown -R frappe:frappe /workspace/health
USER frappe
RUN cd /home/frappe/frappe-bench-image \
 && cp -r /workspace/health apps/health \
 && env/bin/pip install --no-warn-script-location -e apps/health \
 && sed -i -e '$a\' sites/apps.txt \
 && echo "health" >> sites/apps.txt

# ── Stage 3: final image — runtime scripts only ──────────────────────────────
# Scripts change often; isolating them here means edits only rebuild these
# COPY layers, not the slow bench/get-app stages above.
FROM bench-builder

USER root
COPY microservice-deployment/test/init-backend.sh /workspace/init-backend.sh
COPY microservice-deployment/test/entrypoint.sh /workspace/entrypoint.sh
RUN chmod +x /workspace/init-backend.sh /workspace/entrypoint.sh

ENTRYPOINT ["/workspace/entrypoint.sh"]
