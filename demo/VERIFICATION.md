# Client Demo — Verification Record

**Date:** 9 October 2026 (UTC)  
**Target:** the repository's Odoo 17 Community HSE suite  
**Facility:** Northstar Petrochemicals, entirely fictional

## Executed checks

| Check | Result |
|---|---|
| Actual Odoo/PostgreSQL install | Successful installation of the complete dependency graph: 47 modules |
| Fresh-database regression suite | **110 tests; 0 failures, 0 errors** across HSE, meetings, frontline portal and demo suites |
| Latest upgrade/regression run | **111 tests; 0 failures, 0 errors** on a separate test database |
| Presenter-authorized catalog | **73 / 73 ready areas**, 14 domains, **160** primary/reference records, no readiness issues |
| Narrative coverage | Eight journeys, 49 steps, 80-minute narrative / 90-minute full session |
| Native backend metadata | **106** window actions resolved; **100** backend form views loaded, 99 with existing hero styling |
| Record-based reports | **22** report definitions rendered as HTML, including the ten featured previews |
| Parameterized reports | All **six** date/dept summaries generated real rows and rendered HTML; inclusive end-day and timezone behavior tested |
| Browser sample forms | All **73** native sample forms loaded under the normal presenter account |
| Browser reporting | Ten authenticated HTML endpoints returned populated reports; browser-print walkthrough PDF generated |
| Browser usability | Search, empty results, domain filter, notes, checklist persistence/reset, dashboard and 390-pixel layout passed |
| Authorization | Anonymous hub requests require login; contractor hub/guide/coverage requests return 403; own seeded submissions displayed |
| Embedded HTTPS sign-in | Actual cross-site iframe browser test passed with Secure/HttpOnly/partitioned session transport |
| Preview sign-in with blocked cookies | Both role links opened top-level tabs and authenticated while the test proxy deliberately removed iframe cookies |
| CSRF retained | Deliberately invalid CSRF login submission still rejected with HTTP 400 in that iframe test |
| Seed safety | Loader idempotence and edit preservation passed; XML relationship targets validated by model, not coincidental numeric IDs |
| Config/source checks | Compose specification schema and isolation assertions passed; secret generator mode/preservation, Python/XML/JS/shell syntax and Git whitespace checked |
| Explicit provisioning | Password/branding/homepage provisioning executed successfully through actual Odoo shell in isolated demo databases |

The record-report smoke initially skips six input-only wizard models because there are no persisted parameter records. A separate regression supplies real dates/departments, invokes their native actions and verifies **all six** summaries. It does not fabricate business data merely to fill report-input forms.

Browser verification used **Playwright 1.64.0 with Chromium 153** on Linux. The iframe check used a local TLS proxy and a second, cross-site HTTPS origin, with browser web security enabled. It validated both successful authentication and rejection of an invalid CSRF token. This was a real browser check, not just an inspection of response headers.

## Native defects corrected during verification

- Hazard matrix aggregation and click navigation now use the real `likelihood` field.
- Spatial radar no longer counts identical coordinates in unrelated modeled locations as a collision.
- Stop-work sample supervisor references an employee rather than a user with a coincidentally matching numeric ID.
- Legacy corrective reporting uses its actual description field; hazard control labels use `control_measure`.
- Date-filtered reports include the whole selected local end day, reject invalid/incomplete ranges and no longer print report data to stdout.
- Meeting report input dates use ISO values and actual meeting timestamp filtering.
- Dependent-addon integration tests run after installation; meeting attendance expectations use employees present as the denominator.
- Standalone hub action metadata resolves with narrowly elevated, curated action access; business samples/counts remain under caller rights.
- Mobile readiness download buttons wrap rather than forcing horizontal overflow.

## Embedded preview compatibility

Odoo's default login/backend framing policy and default browser cookie handling can reject authentication inside a cross-site preview frame. The demo addon has an **opt-in** compatibility path:

- Disabled by default; normal deployments retain standard Odoo framing/session policy.
- Requires `hse_demo_data.preview_partitioned_sessions` to be explicitly enabled.
- Restricted to declared HTTPS preview origins on `*.e2b.app`; upstream HTTP is trusted only when its host matches the configured HTTPS public origin. A request from any other host — including `http://localhost:8069` — never enters this path.
- Session cookies remain **HttpOnly** and become **Secure**, **SameSite=None**, **Partitioned**.
- Framing is limited to self plus a hard-coded HTTPS host list in `hse_demo_data/models/preview_http.py` (`arena.ai`), not arbitrary websites. **That allowlist is vendor-specific dead code for your own deployment:** if you ever embed the demo on another domain, both the `.e2b.app` test in `preview_cookie_scope()` and that `frame-ancestors` list must be edited deliberately. Nothing needs changing for a local or same-origin hosted demo.
- Authentication, role checks and CSRF validation are not disabled.

The initial TLS iframe test proved this opt-in transport under its test browser/proxy, but did **not** establish that every real hosted browser would return the cookie. Actual hosted request diagnostics subsequently confirmed no session cookie on either the login GET or POST, so refreshing could not fix that environment.

The hosted welcome page now opens each role's sign-in in a **new top-level tab by default**. Its notice tells the presenter to continue there. A follow-up browser/proxy test deliberately removes cookies from iframe navigations, clicks the actual role cards, verifies that they create a top-level page and successfully authenticates both accounts. The flow retains standard passwords and CSRF; no session identifier or authentication token is put in a URL.

No deployment of this repository enables that mode by default. It was turned on only for the temporary cross-site preview used during verification. An operator can opt in during explicit provisioning with `DEMO_PREVIEW_EMBEDDED=1`. Ordinary localhost and non-preview deployments retain same-tab sign-in and standard Odoo framing, so nothing has to be configured for a machine-local run. Users whose browser blocks new windows should open the role's sign-in link in a new tab or paste its URL into the address bar.

## Not executed / not claimed

- **Docker Compose startup, container image build and reset were not executed in the environment that prepared this kit**: no container runtime was available there. The files were validated statically against the Compose specification and shell syntax. Run them once on the target host with the [first-run checklist](LOCAL.md#first-run-checklist) and record the result below.
- **Native Odoo/wkhtmltopdf PDF generation was not executed**: wkhtmltopdf was absent in that environment. HTML and Chromium/browser printing are verified, not native server PDF.
- The official Odoo 17 image is intended to supply wkhtmltopdf. Its historical Dockerfile includes that package, but this does not replace an actual container/PDF test in the target environment.
- No production security/privacy assessment, engineering certification, regulatory filing, physical gate integration or external ERP/CMMS/mail/SMS integration was performed.
- Internal model ACLs remain broad. Medical-data privacy, company separation and segregation of duties need a production review.
- PSSR completion is computed; the current commissioning action still has **no enforcing PSSR gate**. This limitation is disclosed in the hub and walkthrough.
- Unbound legacy spreadsheet generators are not presented as completed client-ready XLSX reports.

## Runtime and reproducibility notes

The verification runtime used downloaded source Odoo 17, Python 3.11 and a portable PostgreSQL instance. The Odoo source branch download and the supplied Docker tags are **not commit/digest-pinned**. This is a verified development demo, not a reproducible production security baseline or version-support promise.

Runtime environments, databases, sessions, generated PDFs/screenshots, logs and credentials are excluded from the Git change set. The committed kit contains the addon code, synthetic diagrams, walkthrough, configuration templates and repeatable commands. Use the [README](../README.md) and the [localhost runbook](LOCAL.md) to reconstruct a new isolated environment rather than relying on any runtime state from the environment that prepared this kit.

## Synthetic assets and local-execution notes

- The four images under `hse_demo_data/static/demo/` are vector-style placeholders generated for this repository, watermarked as non-photographic. They satisfy the seed loader and the branding/favicon references on a fresh clone; they are not client artwork and should be replaced before any external presentation that shows them. The two observation photos are intentionally different images, which `hse_demo_data/tests/test_client_demo.py` asserts.
- `.gitattributes` pins `*.sh`, `*.conf`, `*.py`, `*.xml` and friends to LF. Without it, a Windows clone with `core.autocrlf=true` yields container-mounted scripts that fail on `$'\r'`.
- The Compose port mapping binds `127.0.0.1` by default via `DEMO_HTTP_BIND`, so a laptop run is not exposed to the local network; `0.0.0.0` is an explicit choice.
- `demo/bootstrap.sh` probes `pg_database`/`ir_module_module` before deciding anything, because `docker compose up` re-creates the one-shot `demo-init` service on every start. It runs `--init` only when the demo is not installed yet, and otherwise exits without touching the database — a refresh failure there would otherwise block `web`, which waits for it. Provisioning is likewise limited to first initialization unless `DEMO_REPROVISION=1`. That branch logic was exercised here with stubbed `odoo`/`python3` across the `missing`, `empty`, `uninstalled` and `installed` states; the real install behind each state was not.


Useful local evidence (ignored, not shipped as product files): `test-release.log`, `test-final-policy.log`, `browser-complete.log`, `check-demo-final.log`, `verify-guide.log` under `.local/`, and screenshots/browser-print output under `.demo-runtime/browser/`.
