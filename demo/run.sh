#!/usr/bin/env bash
set -euo pipefail
source /mnt/demo/common.sh
exec odoo "${ODOO_ARGS[@]}"
