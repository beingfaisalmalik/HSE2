#!/usr/bin/env python3
"""Generate private demo secrets without overwriting an existing configuration."""
from pathlib import Path
import os
import secrets


def main():
    path = Path(__file__).resolve().parents[1] / '.env'
    if path.exists():
        print('.env already exists; preserved. Check it against demo/.env.example if needed.')
        return
    values = {
        'DEMO_DATABASE': 'hse_client_demo',
        'DEMO_HTTP_PORT': '8069',
        'DEMO_HTTP_BIND': '127.0.0.1',
        'DEMO_BASE_URL': 'http://localhost:8069',
        'POSTGRES_PASSWORD': secrets.token_urlsafe(24),
        'DEMO_ADMIN_PASSWORD': secrets.token_urlsafe(24),
        'DEMO_PRESENTER_PASSWORD': secrets.token_urlsafe(18),
        'DEMO_PORTAL_PASSWORD': secrets.token_urlsafe(18),
    }
    # Exclusive creation protects existing operator-supplied secrets, even when
    # two setups are launched concurrently. Restrict permissions from creation.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as handle:
        handle.write('# Private credentials for an isolated fictional demo only.\n')
        handle.write('\n'.join('%s=%s' % pair for pair in values.items()) + '\n')
    print('Created private .env (mode 0600). Use it to retrieve demo login passwords; do not commit it.')


if __name__ == '__main__':
    main()
