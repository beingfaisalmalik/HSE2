#!/usr/bin/env bash
set -euo pipefail
source /mnt/demo/common.sh
: "${DEMO_PRESENTER_PASSWORD:?Set DEMO_PRESENTER_PASSWORD}"
: "${DEMO_PORTAL_PASSWORD:?Set DEMO_PORTAL_PASSWORD}"

# `docker compose up` re-creates this one-shot service every time the stack is
# started, so the recorded module state decides whether the demo is initialised at
# all. Repeating --init against an installed demo would re-run install data that
# the presenter may have edited during a session.
state=$(python3 - <<'PY'
import os
import psycopg2

database = os.environ['DEMO_DATABASE']
connection = psycopg2.connect(dbname='postgres', host=os.getenv('HOST', 'db'),
                              port=os.getenv('PORT', '5432'), user=os.getenv('USER', 'odoo'),
                              password=os.environ['PASSWORD'], connect_timeout=20)
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (database,))
        if not cursor.fetchone():
            print('missing')
            raise SystemExit
        cursor.execute("SELECT 1 FROM information_schema.tables "
                       "WHERE table_name = 'ir_module_module'")
        if not cursor.fetchone():
            print('empty')
            raise SystemExit
        cursor.execute("SELECT state FROM ir_module_module WHERE name = 'hse_demo_data'")
        row = cursor.fetchone()
        print(row[0] if row else 'uninstalled')
finally:
    connection.close()
PY
)

if [[ "$state" == 'installed' ]]; then
    # Starting the demo must not mutate it. A refresh that fails would leave this
    # one-shot service non-zero and block `web`, which waits for it to complete.
    echo "hse_demo_data is already installed on $DEMO_DATABASE; leaving the database untouched."
    echo "After changing addon code, run: bash /mnt/demo/update.sh   (or set DEMO_REPROVISION=1 to re-provision)"
else
    echo "Initializing the isolated HSE client demo: $DEMO_DATABASE (module state: $state)"
    odoo "${ODOO_ARGS[@]}" --init=hse_demo_data --without-demo=all --stop-after-init --no-http
fi

# Provisioning writes account credentials and fictional branding and invalidates
# live login sessions, so it runs on first initialization and afterwards only on
# explicit request, never as a side effect of restarting the stack.
if [[ "$state" == 'installed' ]]; then
    case "${DEMO_REPROVISION:-}" in
        1 | true | yes)
            echo 'DEMO_REPROVISION is set; reapplying credentials and branding.'
            ;;
        *)
            echo 'Demo already provisioned. Set DEMO_REPROVISION=1 to reapply .env credentials and branding.'
            exit 0
            ;;
    esac
fi
odoo shell "${ODOO_ARGS[@]}" --no-http < /mnt/demo/provision_demo.py
