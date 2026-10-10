# HSE Enterprise Suite — Comprehensive Client Demo

A working **Odoo 17 Community** demonstration built around **Northstar Petrochemicals**, a fictional industrial facility. It uses the suite's actual models, permissions, forms, workflows and reports — not a mock interface.

> **Demo databases only.** All personnel, health records, plant measurements, contacts, identifiers and financial values are synthetic. This is not an operational safety system, certified engineering assessment or proof of regulatory compliance.

## What is included

- **73 populated module areas across 14 domains**, with searchable registers and native sample-record links.
- **Eight connected journeys / 49 presentation steps**: 80 minutes of walkthrough, or a 90-minute session with introduction and Q&A.
- **160 primary/reference records** in the pristine module explorer, plus child evidence, configuration, HR and portal records. Counts change when you use the app.
- A branded welcome page, restricted presenter hub, live executive dashboard and a separate contractor portal experience.
- Ten featured live report previews; native legacy reports and six date-filtered summaries are also covered by regression tests.
- Downloadable presenter notes, coverage CSV, browser-only presentation checklist, responsive layout and printable journeys.
- Repeatable Docker setup, private credential generation, explicit update/reset procedures and automated checks.

**Start with [the client walkthrough](demo/CLIENT_WALKTHROUGH.md).** The technical checks and limitations are recorded in [verification notes](demo/VERIFICATION.md).

## Entry points and accounts

| Experience | Path | Login |
|---|---|---|
| Role selection, no business data exposed | `/hse/demo/welcome` | No login required |
| Presenter hub, journeys and reports | `/hse/demo` | `hse.presenter` |
| Contractor self-service | `/hse/portal` | `hse.contractor` |
| Personal contractor submissions | `/hse/portal/my-submissions` | `hse.contractor` |
| Current-database walkthrough download | `/hse/demo/guide` | Presenter only |
| Coverage CSV download | `/hse/demo/coverage.csv` | Presenter only |
| Native Odoo backend | `/web` | Presenter or administrator |

Passwords are **not committed or preset by the addon**. Every installation uses only the values in your own private `.env`, so a fresh clone has no usable credential until you generate one below.

Use **separate browser/private windows** for the two roles. The contractor is a portal user, not an internal user, and cannot access the presenter hub or its downloads.

On `http://localhost` sign-in stays in the **same tab**, which is what a laptop or projected demo needs. Two opt-in flags exist only for an **embedded** demo hosted behind a cross-site HTTPS frame that withholds third-party cookies: `DEMO_PREVIEW_EMBEDDED=1` during explicit provisioning switches to partitioned session transport and opens each role's sign-in in a separate top-level tab, and an operator can additionally enable the header-based transport (`hse_demo_data.preview_header_sessions`). Both keep Odoo's normal password, session, ACL and CSRF checks, and no login token or password is placed in a URL. Neither applies to a plain local origin. See [the preview compatibility notes](demo/VERIFICATION.md#embedded-preview-compatibility).

## Quick start on your own machine

You need **Docker Desktop** (Windows, macOS) or Docker Engine with the **Compose v2 plugin** (Linux), plus **Python 3** for secret generation — `python` on Windows. Nothing else goes on the host: PostgreSQL and Odoo both run in containers, and this repository is mounted into them read-only.

```bash
python3 demo/generate_env.py
docker compose -f compose.demo.yml up -d
docker compose -f compose.demo.yml logs -f demo-init web
```

The generator creates a private, mode-`0600` `.env` at the repository root with distinct random credentials and never overwrites an existing file. Compose reads that file automatically because it sits next to `compose.demo.yml`, so no shell sourcing is needed to start the stack. Compare existing settings with `demo/.env.example` and keep `.env` private.

The first run pulls `odoo:17.0` and `postgres:16`, creates the database and installs the 47-module dependency graph — allow a few minutes. Wait for `Demo provisioned` in the `demo-init` logs and for the `web` service to report healthy, then visit **http://localhost:8069**. The default homepage is the role selector.

Retrieve the two login passwords locally from `.env`; do not paste administrator/database credentials into tickets or chat. The native administrator login is `admin`, using `DEMO_ADMIN_PASSWORD`.

Restarting later is cheap and non-destructive: `down` then `up -d` reuses the volumes and leaves the database untouched — it does **not** re-install samples or rewrite passwords and branding. [demo/LOCAL.md](demo/LOCAL.md) covers Windows and PowerShell, port conflicts, logs, reset and troubleshooting.

### Port, host and isolation

- The published port binds to **`127.0.0.1` by default**, so a laptop demo is not reachable from the surrounding network. Set `DEMO_HTTP_BIND=0.0.0.0` in `.env` only when you deliberately want to share it (for example with a projector machine or a hosted VM).
- If port 8069 is occupied, change **both** `DEMO_HTTP_PORT` and `DEMO_BASE_URL` in `.env`, for example to `8070` and `http://localhost:8070`.
- For a hosted demo, set `DEMO_BASE_URL` to the client-facing HTTP(S) origin without a path. Use TLS and private/time-limited access. Browser resources use same-origin relative URLs.
- The Compose project is explicitly named **`hse-client-demo`**. It uses dedicated database and filestore volumes and does not publish PostgreSQL's port.
- The application binds to `0.0.0.0` inside its container, supports a reverse proxy, disables database listing and disables cron in this isolated demo.
- The source is mounted read-only. Initialization installs `hse_demo_data`, whose dependencies install the HSE, meeting, reporting and frontline portal addons.
- Company branding, website homepage and passwords are changed only by the explicitly invoked provisioning script, never by a normal addon install.
- Changing `.env` alone does not change existing Odoo account passwords. Reapply them with `DEMO_REPROVISION=1` and one `demo-init` run. PostgreSQL initialization passwords also do not automatically rotate on an existing volume.

The official Odoo image is intended to provide native PDF support. **These files were validated statically here — Compose schema and anchors, shell/Python/XML/JS syntax, manifest and external-ID references — and the containers themselves were not started, because Docker is absent in this working environment.** HTML report previews and browser printing were verified against a real install; confirm native wkhtmltopdf output on your own host with [the checklist in demo/LOCAL.md](demo/LOCAL.md#first-run-checklist).

## Present the story

| Journey | Audience | Minutes |
|---|---|---:|
| From incident to lasting learning | HSE manager | 12 |
| Authorize work, not uncontrolled risk | Work / operations coordinator | 12 |
| Engineer safer change | Process safety / engineering | 12 |
| Contain, recover and report | Environmental specialist | 9 |
| A qualified workforce, inside and out | Workforce / contractor coordinator | 8 |
| Healthy people, a resilient site | Occupational health / emergency lead | 10 |
| Make compliance evidence visible | Assurance / governance lead | 10 |
| Reliability with measurable return | Asset / operations manager | 7 |

In the hub, enable **Presenter notes**, expand a journey and open its records in new tabs. Search/filter the module explorer for the rest of the suite. **Mark demonstrated** is a personal `sessionStorage` checklist — it does not complete a business workflow.

Workflow buttons **do change real demo records**. In particular, closing entry, starting work, verifying PSSR lines, evaluating training matrices and generating actions change the original story. Rebuild an isolated database for a pristine repeat rather than expecting an upgrade to undo edits.

Native report wizards ask for dates/departments instead of having seeded parameter records. Creation-date summaries include the whole selected end day in the user's timezone; the meeting summary filters actual meeting timestamps.

## Stop, resume, update and reset

### Stop without deleting the demo

```bash
docker compose -f compose.demo.yml stop web
# Resume:
docker compose -f compose.demo.yml up -d web
```

### Apply changed addon code while preserving samples and passwords

Stop the web service during maintenance, then run the explicit update command:

```bash
docker compose -f compose.demo.yml stop web
docker compose -f compose.demo.yml run --rm --no-deps demo-init bash /mnt/demo/update.sh
docker compose -f compose.demo.yml up -d --no-deps web
```

Demo external IDs are `noupdate`; the comprehensive loader is idempotent and preserves existing presenter edits and the original date anchor. XML views/actions and normal addon metadata update as usual. Do not use this procedure as a pristine-data reset.

To intentionally reapply `.env` account credentials and fictional branding, stop the web service and rerun the `demo-init` bootstrap with the explicit opt-in, which the bootstrap otherwise skips for a provisioned database:

```bash
DEMO_REPROVISION=1 docker compose -f compose.demo.yml run --rm --no-deps demo-init
```

In PowerShell use `$env:DEMO_REPROVISION = "1"` on the line before it. This invalidates existing login sessions. Changing a PostgreSQL password on an existing volume requires a matching database-role password change, not just an environment edit.

## Synthetic evidence images

Four small placeholders under `hse_demo_data/static/demo/` keep a fresh clone self-contained:

| File | Where it appears |
|---|---|
| `blocked_walkway.png` | hazard photo on the frontline portal observation sample |
| `unguarded_coupling.png` | hazard photo on the presenter observation sample |
| `northstar_logo.png` | company logo, applied by explicit provisioning only |
| `northstar_mark.png` | browser tab icon on the welcome page and the hub |

They are deliberately vector-style diagrams watermarked **"Synthetic demo diagram — not a photograph"**, so the demo never implies it holds real incident evidence. Replace them with your own artwork whenever you like: keep the file names and the PNG format, and keep the two observation images different from each other, which a regression test asserts.

The two hazard photos are copied into record fields by the loader, so replacing a file does not by itself change the database, and that loader step runs once and then defers to a marker record. Re-apply it explicitly:

```bash
docker compose -f compose.demo.yml run --rm --no-deps demo-init bash -c \
'source /mnt/demo/common.sh
odoo shell "${ODOO_ARGS[@]}" --no-http <<PY
marker = env.ref("hse_demo_data.dd_enrichment_marker", raise_if_not_found=False)
if marker:
    marker.unlink()
env["hse.demo.loader"].load_comprehensive_demo()
env.cr.commit()
PY'
```

That rewrites the enriched sample fields, so it also refreshes their relative dates and the seeded-date note shown in the hub; presenter edits to those specific records are lost. Branding images need no such step — rerun provisioning with `DEMO_REPROVISION=1` above instead. Hard-reload the browser afterwards, because static responses are cached.

### Pristine, fresh-dated reset — destructive

**This deletes the isolated demo's databases, files, accounts and presentation edits. Back up both PostgreSQL and the Odoo filestore if anything must be retained. Never point these volumes at production.**

```bash
docker compose -f compose.demo.yml down --volumes
docker compose -f compose.demo.yml up -d
```

The next initialization anchors all sample dates to the new installation. Your private `.env` is retained, so the same configured passwords are provisioned again.

## Automated verification

### Odoo regression suite

```bash
docker compose -f compose.demo.yml --profile tests run --build --rm demo-test
```

The test service builds a small image with `odoo-test-helper==2.1.3`, which the OCA dependency needs while collecting tests. It **recreates only the disposable `hse_demo_test` database** each run; it never tests against the presenter database. Do not run concurrent test containers against that same database.

The verification recorded in [demo/VERIFICATION.md](demo/VERIFICATION.md) used source Odoo 17, a separate PostgreSQL test database and the equivalent `--test-enable --test-tags='/hse,/hse_demo_data,/hse_meeting,/observation_portal'` command. Re-run it on your own machine with the command above to reproduce it against these images; that file also separates executed results from unexecuted deployment claims.

### Optional read-only browser checks

Requires Node.js 22+ and a compatible Chromium installation. The smoke script reads `DEMO_BASE_URL` and both passwords from the **environment** — Compose does not export `.env` to a host-side Node process, so load it yourself first.

Bash (Linux, macOS, Git Bash, WSL):

```bash
(cd demo/browser && npm ci && npx playwright-core install chromium)
set -a
. ./.env
set +a
npm --prefix demo/browser test
```

PowerShell (Windows) — `set -a` is a bash builtin, so parse the file instead:

```powershell
Push-Location demo/browser; npm ci; npx playwright-core install chromium; Pop-Location
Get-Content .env | Where-Object { $_ -match '^([A-Z_]+)=(.*)$' } | ForEach-Object {
    Set-Item -Path "Env:$($Matches[1])" -Value $Matches[2]
}
npm --prefix demo/browser test
```

On Linux, install Chromium's system dependencies if requested by Playwright. `DEMO_CHROMIUM_PATH` can select an existing compatible binary. For checks running on the server rather than in a remote client, override `DEMO_BASE_URL` with the reachable local origin. The default loopback `DEMO_HTTP_BIND` is fine here, because the browser runs on the same machine.

The smoke script checks all 73 sample forms, ten HTML reports, the dashboard, filters, checklist persistence/reset, 390-pixel layout, browser printing and contractor authorization. Screenshots and its browser-print PDF go to ignored `.demo-runtime/browser/`, not source control. These checks do not exercise native server PDF generation.

## Existing Odoo installation

Use a **new isolated demo database** with this repository on `addons_path`, then install `hse_demo_data`. Its samples are ordinary install data, so they are loaded even with `--without-demo=all`.

Provision credentials and branding explicitly through Odoo shell after exporting the private settings:

```bash
odoo shell -c /path/to/your-demo.conf -d hse_client_demo --no-http < demo/provision_demo.py
```

Use a proper database login, protect the database-manager password, disable outbound integrations/cron and configure the proxy for your environment. Installing the addon alone creates role logins but **does not assign shared passwords, rebrand a real company or change an existing website homepage**.

## Transparent boundaries

- PSSR completion is computed, but the current commissioning action does **not** enforce a PSSR gate. The walkthrough explicitly distinguishes verification from an enforced block.
- SIMOPS, LOTO clearance, preparation readiness, entrant closure and critical-lift exercises use genuine native checks. They are not physical safety interlocks.
- Spatial radar comparisons are scoped to the same modeled location, using synthetic coordinates — not live geolocation or adjacent-zone hazard certification.
- Internal HSE ACLs are broad. Production medical-data privacy, company separation and segregation of duties require review and hardening.
- Medical examples, SDS text, exposure limits, environmental factors, consequence calculations and monetary assumptions require site-specific professional validation.
- No real mail/SMS, agency submission, physical access gate or external ERP/CMMS integration is configured. Do not connect this fictional database to those services.
- The existing repository targets Odoo 17. Its source/runtime images are not digest-pinned, and this demo is not a commitment to the version's ongoing security support or a production upgrade plan.

## Implementation map

- `hse_demo_data/seed.py`: connected fictional evidence with stable external IDs.
- `hse_demo_data/demo_catalog.py`: all module areas, eight journeys and featured reports.
- `hse_demo_data/services.py` / `controllers/`: caller-authorized catalog and restricted downloads.
- `hse_demo_data/views/` / `static/`: branded welcome, guided hub, responsive styles and synthetic diagrams.
- `demo/`: deployment, provisioning, maintenance, client walkthrough and QA tooling.
- `hse_demo_data/tests/`: coverage, evidence chains, actual gates, idempotence, role isolation and reporting regressions.

Targeted native defects found during demo verification were corrected: hazard likelihood matrix aggregation/navigation, cross-location radar false positives, mismatched seed relation types, legacy CAPA report fields/controls, inclusive report end dates, meeting report date serialization and test lifecycle/attendance expectations.
