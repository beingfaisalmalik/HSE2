# -*- coding: utf-8 -*-
{
    'name': "HSE Safety Dashboard",
    'summary': "Excel-grade Safety Dashboard: injury/near-miss/UAC/incident logs, corrective actions, PTW register, KPI rates and data-health checks",
    'description': """
HSE Safety Dashboard — Odoo conversion of the client's Excel "Safety Dashboard" workbook.
=========================================================================================

Registers (entry sheets, mirroring the Excel columns 1:1)
---------------------------------------------------------
* Injury Log            (INJ-xxx) — type, department, lost workdays, root cause, CA link, status
* Near Miss Log         (NM-xxx)  — potential severity, reported by, CA link, status
* Unsafe Act/Condition  (UAC-xxx) — act vs condition, immediate action, CA link, status
* Incident Log          (INC-xxx) — non-injury incidents with estimated impact
* Corrective Actions    (CA-xxx)  — workflow Open -> In Progress -> Closed, target date, overdue flag
* PTW Register          — permits with work-type tags (Hot/Cold Work, Height, Electrical, ...)

Monthly inputs
--------------
* One row per month: man-hours, planned/completed inspections, toolbox talks,
  PTW issued, training hours, internal audit score (replaces the Excel
  "KPI Calculations" + "Leading Indicators" input cells).

KPI engine (replaces the hidden Calc / CalcRows sheets)
-------------------------------------------------------
* LTIFR / TRIR / Severity = count x rate-base (200,000 h) / man-hours, n/a without hours
* Month, prior-month, YTD-to-month and full-year figures, computed live from the logs
* Days since last LTI, CA closure rate, PTW register vs entered figure
* 10 data-health checks with a review banner, exactly like the workbook

Dashboards
----------
* Monthly dashboard client action: month selector, KPI cards with deltas, registers
  for the selected month, 12-month chart, data-health banner
* Yearly dashboard: YTD cards, month-by-month table, full health-check table

Reports
-------
* Printable monthly/annual KPI report (QWeb PDF)
* Excel export that regenerates the workbook sheets from live data
* Excel import wizard that reads the original workbook (both PTW layouts,
  d/m/y text dates handled like the CalcRows parser)

Company: Poly Pack Films (Pvt.) Ltd. (or your own — the dashboard reads res.company).
    """,
    'author': "HSE Global Enterprise",
    'website': "https://www.yourcompany.com",
    'category': 'Human Resources/HSE',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/dashboard_action.xml',
        'views/settings_views.xml',
        'views/injury_views.xml',
        'views/near_miss_views.xml',
        'views/uac_views.xml',
        'views/incident_views.xml',
        'views/ca_views.xml',
        'views/ptw_views.xml',
        'views/monthly_figure_views.xml',
        'views/report_wizard_views.xml',
        'report/kpi_report_templates.xml',
        'report/kpi_report_actions.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            ('include', 'web.chartjs_lib'),
            'hse_safety_dashboard/static/src/scss/dashboard.scss',
            'hse_safety_dashboard/static/src/js/dashboard.js',
            'hse_safety_dashboard/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
