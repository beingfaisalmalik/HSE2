#!/usr/bin/env bash
set -euo pipefail
export DEMO_DATABASE=hse_demo_test
source /mnt/demo/common.sh
# Always collect the entire installation graph, including at-install tests.
# This constant database is disposable and never the presentation database.
echo 'Recreating the dedicated hse_demo_test database; presentation data is unchanged.'
python3 - <<'PY'
import os
import psycopg2
conn = psycopg2.connect(dbname='postgres', host=os.getenv('HOST', 'db'),
                        port=os.getenv('PORT', '5432'), user=os.getenv('USER', 'odoo'),
                        password=os.environ['PASSWORD'], connect_timeout=15)
conn.autocommit = True
with conn.cursor() as cursor:
    cursor.execute('DROP DATABASE IF EXISTS hse_demo_test')
conn.close()
PY
exec odoo "${ODOO_ARGS[@]}" --init=hse_demo_data --without-demo=all \
    --test-enable --test-tags='/hse,/hse_demo_data,/hse_meeting,/observation_portal' \
    --stop-after-init --http-port=8079
