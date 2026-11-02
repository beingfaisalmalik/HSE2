# HSE Safety Dashboard (`hse_safety_dashboard`)

**Odoo 17 conversion of the client's Excel "Safety Dashboard" workbook — workflows, reports and live dashboards, verified end-to-end.**

Company: Poly Pack Films (Pvt.) Ltd. (or any Odoo company — the dashboard reads `res.company`).

---

## What you get

### 🖥️ Dashboards (client actions)

| Screen | Contents |
|---|---|
| **Monthly Dashboard** | **Dynamic year selector** (options built from the registers themselves) plus a **month selector listing only the months that hold data** for that year, 4 KPI bands of 6 cards each — **Injury Outcomes**, **Exposure & Rates**, **Observations & CAs**, **Leading Indicators** — every card with month-over-month delta (`▲ +N vs Aug-26` / `▼ -N` / `● same` / `– no comparison`) and a YTD line, status strip with data-check count, expandable 10-row data-health table, 12-month Chart.js trend, and the four registers (injuries, near misses, incidents, open CAs) for the selected month. |
| **Yearly Dashboard** | YTD summary cards (man-hours, LTI, recordable, lost workdays, LTIFR/TRIR/severity, days since last LTI), month-by-month table (12 rows × 15 columns, PTW entered/register with `≠` flag), full data-health table — year selector applies here too. |

### 📋 Workflows

* **Corrective Actions**: `Open → In Progress → Closed` state machine with buttons, auto closure date, **overdue flag** (open past target), scheduled activity on the target date, chatter for collaboration.
* **All four logs**: Open/Closed status buttons, chatter + activities, unique IDs (`INJ-001`, `NM-001`, `UAC-001`, `INC-001`) from sequences.
* **PTW register**: open/closed/expired status.
* **Monthly Figures**: one row per (year, month) — man-hours + all leading indicators, unique constraint per month.

### 📊 KPI engine (replaces hidden Calc/CalcRows)

Pure live Python over the registers — no stored snapshot, no `#REF!`, ever:

* `LTIFR = LTI × base / man-hours`, `TRIR = recordable × base / hours`, `Severity = lost workdays × base / hours` — **n/a when no hours** (Excel `IF(E>0, …, "")`).
* `Recordable = LTI + MTC` (First Aid excluded).
* **YTD rates only sum months that have man-hours** (Excel `SUMIFS(…, has_hours=1)` rule).
* CAs attributed to the month of their **linked event's date** (Excel `CalcRows AO/AP` resolution order).
* Days since last LTI as of month-end (or today), fallback = days since Jan 1.
* PTW keyword counts (`*Hot Work*`, `*Work at Height*`, `*Electrical*`, `*Confined*`, `*Radioactiv*`, `*Crane*`, `*Cold Work*`, `*Excavation*`).

### 🩺 Data-health checks (10, exact Calc r145–r154 semantics)

1. Missing / unreadable / outside-year dates (per register, with detail counts)
2. Dates typed as text — *impossible in Odoo: true date fields*
3. Future-dated entries (day/month swap heuristic)
4. Out-of-chronological-order entries (by log ID sequence)
5. CAs whose *Related Log Entry ID* has no dated match
6. Open CAs with no target date
7. Months with events logged but no man-hours entered
8. Invalid unsafe-act type — *impossible: selection field*
9. Months where PTW register rows ≠ PTW issued figure
10. KPI totals differing from dashboard — *impossible: single live source*

Banner: `Showing September 2026 | data checks: 4 item(s) to review`.

### 📄 Reports

Every report is reachable from **Reporting → Generate Reports** (report-type
dropdown), from the wizard's *Print* menu, and — for the workflow reports —
from its own **Reporting → Workflow Reports** menu entry:

* **Monthly Safety Dashboard (PDF)** — KPI table, YTD table, health checks, registers.
* **Yearly Safety Report (PDF)** — YTD summary, 12-month table, health checks.
* **KPI Calculations (PDF, landscape)** — the Excel *KPI Calculations* sheet as a live PDF: injury KPIs & rates, observations/CAs, leading indicators — 12 months + both YTD rows + data health.
* **Leading Indicators (PDF, landscape)** — man-hours, inspections planned/completed/compliance, toolbox talks, PTW issued vs register, training hours, audit score per month + YTD.
* **One report per workflow (PDF, landscape)** — Injury Log · Near-Miss Log · Unsafe Act/Condition · Incident Log · Corrective Actions · PTW Register · Monthly Figures. Each is filtered by **dynamic year / month / department / status** selections; entries that can never fall inside the period (no readable date, or a CA whose related entry has none) are shown in a clearly labelled section instead of being dropped.
* **Excel Workbook (XLSX)** — regenerates `KPI Calculations`, all four logs, `Corrective Actions`, `PTW Register`, `Leading Indicators`, `Data Health` sheets from live data (XlsxWriter), **using the same dynamic filters as the PDFs**.

Dynamic selections: the wizard's **year** list is built from the data
(registers ∪ monthly figures ∪ settings year ∪ current year, newest first);
**department** options are the distinct departments on the registers;
nothing is hardcoded.

### 📥 Excel import wizard

Upload the original `Safety Dashboard - (Template).xlsx` and everything lands in Odoo:

* All six sheets parsed; **both PTW column layouts** (early: location col S/status T + type text in J; later: location Q/status R + type text H).
* d/m/y text dates parsed exactly like CalcRows (`15/03/2026`, `05-Sep-2026`, `12/8/2026`, ISO, Excel serials, 2-digit years → 2000+).
* Existing IDs are skipped → **re-import is safe**.
* Placeholder text (`M/DD/YYYY` closure dates) is **kept empty**, never converted into a fake date.
* Missing CA links (e.g. `CA-073`, `CA-074` referenced by logs but absent from the CA sheet) stay empty and surface in health check 5 — **nothing is invented**.
* Footnote rows in the workbook are ignored (strict `XXX-###` ID pattern).

---

## Data-fidelity commitment

The demo data (`demo/demo_data.xml`) contains the client's **real records exactly as in the workbook**:

* 3 injuries (**dates empty in Excel → imported without dates**, flagged by check 1),
* 1 near miss (2026-04-20), 2 unsafe acts/conditions, 1 incident (all undated as in Excel),
* 5 corrective actions (CA-012 open, target 2026-09-15 → overdue),
* 260 PTW rows (**all undated** — register counts stay 0 vs entered 172/87, exactly like the workbook),
* monthly figures: Mar 22,000 h; Aug 60,192 h + 172 talks/PTW/1 h training + 1/1 inspections; Sep 87 talks/87 PTW/8 h training; Jan audit 0.92.

Missing data is **reported, never fabricated** — that was a standing decision on this project.

---

## Installation

```bash
# Odoo 17
odoo-bin -d <db> -i hse_safety_dashboard --addons-path=<path>,/path/to/this/repo
```

Dependencies: `base`, `mail`, `web` (standard Odoo). Python extras: `openpyxl` (import), `XlsxWriter` (export) — both in Odoo's own requirements.

Groups: **HSE Safety : User** (read + create registers) and **HSE Safety : Manager** (full + settings + import).

---

## Tests

```bash
odoo-bin -d <testdb> -i hse_safety_dashboard --test-enable --stop-after-init
```

* `test_kpi_engine.py` — rate arithmetic, YTD hours-only rule, n/a semantics, attribution, days-since-LTI, dashboard payload shape.
* `test_workflows.py` — CA state machine, overdue, activities, unique IDs, sequences, UAC type constraint.
* `test_health_checks.py` — each of the 10 checks fires exactly when it should (and checks 2/8/10 prove impossible-by-design).
* `test_excel_roundtrip.py` — a miniature workbook (both PTW layouts, three date formats, placeholder closure date, footnote rows) is imported, verified field-by-field, re-imported safely, and then drives the same KPI numbers as the Excel.
* `test_report_options.py` — dynamic year/month/department selections, all 12 report types routing to the right report action, per-workflow row filtering (period · department · status), the undated-entry "unmatched" sections, and the filtered XLSX sheets.

---

## Verification status (2026-11-02, Odoo 17.0 — final)

| Layer | Result |
|---|---|
| Automated suite | **51/51 tests, 0 failures, 0 errors** on a fresh DB (`--test-enable`, includes install + demo) |
| Fresh install | Demo loads exactly: 3 injuries · 1 NM · 2 UAC · 1 INC · 5 CAs · 260 PTW · 12 monthly figures · company `Poly Pack Films (Pvt.) Ltd.` |
| KPI engine vs workbook | Sep-26: 87 talks / 87 PTW / LTIFR n/a (no hours) · Aug-26: 60,192 h / 172 PTW / LTIFR 0.00 · Mar: 22,000 h · Jan audit 0.92 — all match the Excel |
| Data-health | 4 live flags exactly as the workbook: check 1 = 266 undated rows, check 5 = 5 unmatched CA refs, check 7 = 1 month with events but no hours, check 9 = 2 PTW mismatches (Aug, Sep) |
| Dynamic selectors | Dashboard payload over RPC returns `years=[2026]` and `available_months=[1…12]` (data-driven); wizard `fields_get` resolves year/department/report-type selections dynamically; default month = latest month holding data |
| Dashboards (OWL) | Component mounted headless (jsdom + Odoo's OWL build): **32/32 assertions** — cards, deltas, health strip, Chart.js bound via `useRef`, monthly↔yearly switch, health-panel toggle, **year selector + data-driven month options + onYearChange + month-change round-trip** |
| Assets | `dashboard.js`, `dashboard.xml`, `dashboard.scss` all compile into `web.assets_backend` (debug bundle serves `onYearChange` + `hse_year_select`); Chart.js via `web.chartjs_lib` |
| Reports (HTTP) | **55/55 checks**: all **12 report types** route correctly; **11 PDFs** (monthly, yearly, KPI, leading, 7 workflow) render over HTTP with the shim — 36–51 KB each, styled (asset CSS inlined), landscape for the tabular reports; HTML routes OK; XLSX downloads with all 9 sheets; 14 new xmlids registered |
| Report filters | Period (year + optional month), department and status filters verified over HTTP and in unit tests; undated / unmatched entries always surfaced in a labelled section — never dropped, never invented |
| Workflows | CA `Open → In Progress → Closed`, log open/close, sequences, unique IDs — exercised over HTTP |
| XML / Python / JS | All files parse/compile; no stale patterns (`attrs=`, `__owl__`, client-side `is not None`) |

Known environment notes:

* PDF rendering in this sandbox used a `wkhtmltopdf` compatibility shim (xhtml2pdf-based: fetches Odoo's asset CSS, applies the paperformat geometry as `@page`, chunks wide tables defensively). On a normal Odoo 17 deployment the official `wkhtmltopdf` renders these same QWeb templates directly.
* Odoo's XML data loader collapses `%%` → `%` on load (backward compatibility), so percentage formats in QWeb use `'…%'.format(…)` instead of `%`-formatting.
