#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${DEMO_DATABASE:?Set DEMO_DATABASE in your private .env}"
: "${PASSWORD:?Set the database PASSWORD}"
: "${DEMO_ADMIN_PASSWORD:?Set DEMO_ADMIN_PASSWORD}"
if [[ ! "$DEMO_DATABASE" =~ ^[a-z][a-z0-9_]*demo[a-z0-9_]*$ ]]; then
    echo 'Refusing a database name without "demo" or with unsafe characters.' >&2
    exit 1
fi
if [[ ${#DEMO_ADMIN_PASSWORD} -lt 14 || "$DEMO_ADMIN_PASSWORD" == *$'\n'* || "$DEMO_ADMIN_PASSWORD" == *$'\r'* ]]; then
    echo 'The demo administrator password must have at least 14 characters and no line breaks.' >&2
    exit 1
fi
runtime_conf=$(mktemp /tmp/hse-demo-XXXXXX.conf)
cat /mnt/demo/odoo.conf > "$runtime_conf"
printf '\nadmin_passwd = %s\n' "$DEMO_ADMIN_PASSWORD" >> "$runtime_conf"
ODOO_ARGS=(--config="$runtime_conf" --db_host="${HOST:-db}" --db_port="${PORT:-5432}"
           --db_user="${USER:-odoo}" --db_password="$PASSWORD"
           --database="$DEMO_DATABASE" --db-filter="^${DEMO_DATABASE}$")
