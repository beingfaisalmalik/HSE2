#!/usr/bin/env bash
set -euo pipefail
source /mnt/demo/common.sh
# Explicit maintenance step. The comprehensive loader preserves existing samples,
# passwords and the original date anchor; provisioning is not run by updates.
exec odoo "${ODOO_ARGS[@]}" --update=hse,hse_meeting,hse_reports,observation_portal,hse_demo_data \
    --stop-after-init --no-http
