# Running the client demo on your own machine

Everything here runs on the computer you clone this repository to. No hosted preview, no
shared credentials, no dependency on any machine other than yours. PostgreSQL and Odoo both
run inside containers; the repository is mounted into them read-only, so edits to addon source
are picked up without rebuilding an image.

Return to the [README](../README.md) for what the demo contains and how to present it.

## What you need

| Requirement | Notes |
|---|---|
| Docker Desktop (Windows, macOS) or Docker Engine + Compose v2 (Linux) | `docker compose version` must work; the legacy `docker-compose` binary is not used here |
| Python 3 | only to generate `.env`. `python3` on Linux/macOS/WSL, `python` on a stock Windows install |
| ~3 GB free disk | one PostgreSQL volume, one filestore volume, two image pulls |
| A free TCP port | default `8069`; change `DEMO_HTTP_PORT` and `DEMO_BASE_URL` together |

Nothing is installed globally: no Odoo package, no PostgreSQL server, no pip requirements.
Node.js 22+ is only needed for the optional read-only browser checks.

## First run

From the repository root, in Bash (Linux, macOS, Git Bash, WSL):

```bash
python3 demo/generate_env.py          # creates a private .env, mode 0600
docker compose -f compose.demo.yml up -d
docker compose -f compose.demo.yml logs -f demo-init web
```

The same two setup commands in PowerShell:

```powershell
python demo\generate_env.py
docker compose -f compose.demo.yml up -d
docker compose -f compose.demo.yml logs -f demo-init web
```

Then open **http://localhost:8069**. Log in as `hse.presenter` with the value of
`DEMO_PRESENTER_PASSWORD`, or as `admin` with `DEMO_ADMIN_PASSWORD`. Read the passwords back
locally with `grep DEMO_PRESENTER_PASSWORD .env` — never paste them into a ticket or chat.

Compose loads `.env` from the directory holding `compose.demo.yml`, so you do not have to
source it for any `docker compose` command; you only need to export it for host-side tools such
as the browser checks.

### What the first start does

1. `db` starts and is health-checked. Its port is **not** published.
2. `demo-init` runs `demo/bootstrap.sh`, which inspects the target database and, on a fresh
   one, runs `odoo --init=hse_demo_data --without-demo=all --stop-after-init`. Installing that
   one module pulls in the HSE, meeting, reporting and frontline portal addons — 47 modules.
3. `demo-init` then pipes `demo/provision_demo.py` through `odoo shell`, which sets the three
   demo passwords, the fictional Northstar branding, `web.base.url` and `report.url`.
4. `web` starts only after `demo-init` exits successfully (`service_completed_successfully`),
   and `run.sh` launches Odoo with `demo/odoo.conf`.
5. Because `restart` is `"no"` for `demo-init`, the container stays exited with code 0. That is
   the healthy state, not a failure.

Expect roughly two to five minutes on the first run, dominated by the image pulls and module
install. The line to wait for is `Demo provisioned.` in the `demo-init` logs.

On later starts, `demo-init` runs again, sees that `hse_demo_data` is installed, prints a
guidance line and exits without touching the database — deliberately, because a refresh that
failed there would block `web` and because your presentation edits must survive a restart. Use
`bash /mnt/demo/update.sh` after pulling code changes, and `DEMO_REPROVISION=1` to reapply
credentials and branding. See
[Stop, resume, update and reset](../README.md#stop-resume-update-and-reset).

## First-run checklist

Run through this once on a new host so that nothing is assumed from a different environment:

- [ ] `docker compose -f compose.demo.yml ps` shows `db` and `web` healthy and `demo-init` exited 0.
- [ ] `http://localhost:8069` shows the Northstar role selector, with the tab icon from `hse_demo_data/static/demo/northstar_mark.png`.
- [ ] `hse.presenter` reaches `/hse/demo` and the module explorer reports no readiness issues.
- [ ] The executive dashboard renders (this is a live view, not a screenshot).
- [ ] An observation sample shows a hazard photo — the two synthetic diagrams must look different.
- [ ] One featured report opens as HTML from the hub.
- [ ] **Native PDF** downloads from that report. The `odoo:17.0` image is expected to provide
      wkhtmltopdf; if the download fails, note the exact error and see the PDF row below.
- [ ] `/hse/demo/guide` downloads a walkthrough generated from this database.
- [ ] `/hse/portal` works for `hse.contractor`, and the same browser session gets **403** on `/hse/demo`.
- [ ] `docker compose -f compose.demo.yml --profile tests run --build --rm demo-test` ends with 0 failures.

## Everyday commands

```bash
# Follow logs, then stop/start without touching data
docker compose -f compose.demo.yml logs -f web
docker compose -f compose.demo.yml stop
docker compose -f compose.demo.yml up -d

# Apply pulled addon code: refresh the modules, then restart the app. `--no-deps`
# skips the healthcheck wait, so make sure `db` is already running.
docker compose -f compose.demo.yml up -d db
docker compose -f compose.demo.yml stop web
docker compose -f compose.demo.yml run --rm --no-deps demo-init bash /mnt/demo/update.sh
docker compose -f compose.demo.yml up -d --no-deps web

# An Odoo shell against the demo database (credentials come from .env via common.sh)
docker compose -f compose.demo.yml run --rm --no-deps demo-init \
  bash -c 'source /mnt/demo/common.sh && odoo shell "${ODOO_ARGS[@]}" --no-http'
```

Changing view or action XML needs that module refresh; a plain restart will not pick it up,
because `bootstrap.sh` deliberately leaves an installed database alone.

## Reset

`down` keeps both volumes; anything below is destructive to the demo database only — but verify
`docker volume ls` first and never point these volumes at a real database.

```bash
docker compose -f compose.demo.yml down
docker volume ls | grep hse_demo            # confirm what you are about to delete
docker compose -f compose.demo.yml down --volumes
docker compose -f compose.demo.yml up -d
```

Your `.env` survives, so the same accounts and passwords are provisioned again, and every sample
date is re-anchored to the new install date. To rotate a PostgreSQL password on an existing
volume you must also change the database role's password; an `.env` edit alone is not enough.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `python3: command not found` (Windows) | Use `python demo\generate_env.py`, or install from python.org and re-open the terminal. |
| `required variable POSTGRES_PASSWORD is missing a value` | No `.env` next to `compose.demo.yml`. Run the generator, or copy `demo/.env.example` to `.env` and fill it in. |
| `Bind for 127.0.0.1:8069 failed: port is already allocated` | Another Odoo or dev server owns the port. Set `DEMO_HTTP_PORT=8070` and `DEMO_BASE_URL=http://localhost:8070`, then `up -d` again. |
| `bash /mnt/demo/bootstrap.sh: line N: $'\r': command not found` | Your clone used CRLF endings. `demo/` is pinned to LF by `.gitattributes`, so a fresh clone is correct; repair an existing checkout with `sed -i 's/\r$//' demo/*.sh` (Git Bash on Windows) or re-clone. |
| `Refusing a database name without "demo"` | `DEMO_DATABASE` must contain `demo` — a deliberate guard against pointing this kit at a real database. |
| `The demo administrator password must have at least 14 characters` | Shorten-proof rule in `demo/common.sh`. Regenerate `.env` or set a longer `DEMO_ADMIN_PASSWORD`. |
| `FileNotFoundError: 'hse_demo_data/static/demo/...'` during install | The synthetic evidence images are missing from your working copy. Restore them with `git checkout -- hse_demo_data/static/demo`. |
| `Access denied for user "odoo"` or the init container restarts with a DB error | `POSTGRES_PASSWORD` in `.env` no longer matches the existing volume. Either restore that value or reset the volumes as above. |
| `web` never turns healthy after `demo-init` succeeds | Read `docker compose -f compose.demo.yml logs demo-init` and `... logs web`. `workers = 0` in `demo/odoo.conf` means one process; a first-start install can exceed the healthcheck window, so give it a couple of minutes before recreating. |
| `Permission denied` reading `/mnt/extra-addons` (Linux with SELinux) | Bind mounts need a label: add `:z` to the two repository mounts in `compose.demo.yml`, or relax SELinux for that path. |
| Sign-in returns to the login page in a loop | Browse the exact origin in `DEMO_BASE_URL`. If you reach the demo by IP or hostname, set `DEMO_BASE_URL` to that origin, then re-run provisioning with `DEMO_REPROVISION=1`. |
| PDF download fails with a wkhtmltopdf error | Test inside the container: `docker compose -f compose.demo.yml exec web wkhtmltopdf --version`. Use the HTML preview or browser printing meanwhile; do not present an unverified PDF as client-ready. |
| The presenter hub returns 403 | Expected for `hse.contractor`: that account is a portal user. Use separate private windows for the two roles. |
| A colleague cannot open the URL | `DEMO_HTTP_BIND` defaults to `127.0.0.1` so a laptop demo stays private. Set `0.0.0.0` only when you mean to expose it on the network, and prefer a reverse proxy with TLS for anything beyond a trusted LAN. |

## Without Docker (your own Odoo installation)

The demo is an ordinary Odoo 17 addon set, so a normal source or packaged install works.
Requirements are exact, because `hse_demo_data` deliberately does not know where your Odoo lives.

**1. What must be present.** `hse_demo_data` depends on `hse`, `hse_meeting`, `hse_reports` and
`observation_portal`; those in turn need `base_tier_validation`, `base_tier_validation_server_action`
and `report_xlsx` — **all seven ship in this repository**, so no OCA download is needed. Point
`--addons-path` at the **repository root**, not at an addon subfolder: Odoo discovers every addon as a
direct child. The remaining dependencies (`base`, `web`, `mail`, `portal`, `website`, `hr`) come from
Odoo 17 Community itself. `base_geolocalize` and `bus` are only pulled in by the optional
`ks_dashboard_ninja`, and `account` by the optional `account_payment_mode`.

Find your core addons path if you are unsure:

```bash
python3 -c "import odoo, os; print(os.path.dirname(odoo.__file__))"   # .../odoo  -> .../odoo/addons
```

Check the three Python modules that `report_xlsx` and the demo hub import:

```bash
python3 -c "import xlsxwriter, xlrd, cryptography; print('ok')"
```

Install anything missing **into the interpreter that runs Odoo** (`python3 -m pip install …`; on a
Windows installer deployment that is Odoo's own bundled Python, not the system one). The other
repository addons are optional extras for this demo — note that `ks_dashboard_ninja` additionally
requires `pandas`, `xlrd`, `openpyxl` and `gTTS`, which nothing in the required set needs.

**2. Install into a fresh database whose name contains `demo`.** The name is a real guard, not
style: `demo/common.sh` and `demo/provision_demo.py` both refuse any other database. Pass `--init`
only for `hse_demo_data`; Odoo installs its whole dependency chain and creates the database for you
if it does not exist yet (or run `createdb hse_client_demo` first when the role lacks CREATEDB).

```bash
odoo -d hse_client_demo \
     --addons-path=/path/to/HSE2,/path/to/odoo/addons \
     --without-demo=all --init=hse_demo_data --stop-after-init --no-http
```

`--without-demo=all` keeps Odoo's own demo rows out of the record counts the hub reports; the HSE
samples are ordinary install data in `hse_demo_data/data/`, so they load regardless.

**3. Provision credentials, branding and the homepage.** This step is what sets the three demo
passwords, the fictional company, `web.base.url` and `report.url`, and points the website root at
`/hse/demo/welcome`. Without it the accounts exist but share no password, and `/` shows the stock
website — use `http://localhost:8069/hse/demo/welcome` directly.

```bash
set -a; . ./.env; set +a          # bash: load DEMO_* from your private .env
odoo shell -d hse_client_demo \
     --addons-path=/path/to/HSE2,/path/to/odoo/addons \
     --no-http < demo/provision_demo.py
```

`odoo shell` must run as the superuser environment it creates by default, and the script raises a
clear `ValueError` if a password is shorter than 14 characters, if two accounts share one, if
`DEMO_BASE_URL` carries a path or credentials, or if `hse_demo_data` is not installed yet.

**PowerShell has no `<` redirection** and no `set -a`, so do this instead:

```powershell
Get-Content .env | Where-Object { $_ -match '^([A-Z_]+)=(.*)$' } | ForEach-Object {
    Set-Item -Path "Env:$($Matches[1])" -Value $Matches[2]
}
Get-Content demo\provision_demo.py | odoo shell -d hse_client_demo `
  --addons-path=C:\path\to\HSE2,C:\path\to\odoo\addons --no-http
```

**4. Run it.**

```bash
odoo -d hse_client_demo \
     --addons-path=/path/to/HSE2,/path/to/odoo/addons \
     --without-demo=all --db-filter='^hse_client_demo$' \
     --http-port=8069 --workers=0 --max-cron-threads=0
```

`--max-cron-threads=0` is not cosmetic: the demo must never run scheduled notifications, which is
also why `demo/odoo.conf` sets `max_cron_threads = 0`. Add `list_db = False` and a real
`admin_passwd` in your own config file, and `--proxy-mode` only when a reverse proxy fronts Odoo.

**5. `report.url` follows the port, not the host.** Provisioning writes
`report.url = http://127.0.0.1:8069` because the server-side PDF worker must reach Odoo through
loopback. If you run on another port, change it in *Settings → Technical → System Parameters*
(or the PDF action will time out or return an empty report while HTML previews still work):

```bash
odoo shell -d hse_client_demo --addons-path=... --no-http <<< \
  "env['ir.config_parameter'].sudo().set_param('report.url','http://127.0.0.1:8079'); env.cr.commit()"
```

### Updating and re-seeding without Docker

```bash
odoo -d hse_client_demo --addons-path=... -u hse,hse_meeting,hse_reports,observation_portal,hse_demo_data --stop-after-init
```

That re-runs `hse_demo_data/data/90_comprehensive_demo.xml`, i.e. the loader. It is idempotent and
skips records you have edited, and `_enrich_existing_scenarios()` defers to the
`dd_enrichment_marker` parameter — which is why replacing a hazard image file needs the
marker-reset snippet in the [README](../README.md#synthetic-evidence-images) rather than an update.

### Regression tests without Docker

`base_tier_validation` and `base_tier_validation_server_action` import `odoo_test_helper` at test
collection time even when you select only the HSE modules, so install it first
(`pip install odoo-test-helper==2.1.3`; `freezegun` is needed by the reminder test). Use a throwaway
database, never the presentation one:

```bash
createdb hse_demo_test
odoo -d hse_demo_test --addons-path=/path/to/HSE2,/path/to/odoo/addons \
     --without-demo=all --init=hse_demo_data --test-enable \
     --test-tags='/hse,/hse_demo_data,/hse_meeting,/observation_portal' \
     --stop-after-init --http-port=8079
```

Expect **0 failures**; the last run recorded in [VERIFICATION.md](VERIFICATION.md) was 111 tests.


## Verifying on your host

`compileall` and `py_compile` are deliberately **not** suggested here: this repository tracks
`__pycache__/*.pyc` files (182 of them), so generating bytecode would dirty your working tree.
Parse the sources instead, which writes nothing:

```bash
python3 - <<'EOF'
import ast, pathlib, sys
skipped = {'.git', 'node_modules', '.demo-runtime', '.local'}
bad, checked = [], 0
for path in pathlib.Path('.').rglob('*.py'):
    if skipped.intersection(path.parts):
        continue
    checked += 1
    try:
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    except SyntaxError as error:
        bad.append(f'{error.filename}:{error.lineno}: {error.msg}')
for problem in bad:
    print(problem)
print(f'Parsed {checked} Python files with {len(bad)} syntax errors.')
sys.exit(1 if bad else 0)
EOF
```

```bash
bash -n demo/*.sh                                              # container-mounted scripts
python3 -c "import glob, xml.dom.minidom as x; [x.parse(f) for f in glob.glob('**/*.xml', recursive=True)]; print('XML parsed')"
docker compose -f compose.demo.yml --profile tests config -q    # interpolation + schema
docker compose -f compose.demo.yml --profile tests run --build --rm demo-test
(cd demo/browser && npm ci && npx playwright-core install chromium) && npm --prefix demo/browser test
```

The first four commands are read-only and safe to repeat. The last two need the stack: the Odoo
test service recreates only the disposable `hse_demo_test` database, and the browser checks drive
the running `web` service through `.env` values exported in your shell.

`demo/VERIFICATION.md` separates what has been executed against a real install from what is
declared but unexecuted, and records the residual limits of the demo. Update that file with your
own results rather than trusting any claim in it about a container run you have not made.
