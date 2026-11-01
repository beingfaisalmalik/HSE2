# -*- coding: utf-8 -*-
{
    'name': "hse_reports",

    'summary': "Enterprise HSE report suite: incidents/OSHA 300, audits, compliance, competency matrix, statutory certs, monthly KPIs",

    'description': """
Enterprise HSE Reporting Suite
------------------------------
- Record-based QWeb reports: permit to work, LOTO plans, HAZOP studies,
  audits, compliance register, competency matrix, statutory certificates,
  OSHA 300 log and monthly HSE KPI
- Date-parameterized summary wizards (RA/JSA, observations, incident
  reporting, incident investigation, legacy CAPA) with HTML/PDF output
- XLSX spreadsheet exports for the RA/JSA and observation summaries
    """,

    'author': "HSE Global Enterprise",
    'website': "https://www.yourcompany.com",

    'category': 'Human Resources/HSE',
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hse','report_xlsx'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/ra_jsa_report.xml',
        'views/observation_report.xml',
        'views/incident_reporting_report.xml',
        'views/incident_investigation_report.xml',
        'views/corrective_report.xml',
        'views/preventive_report.xml',
        'wizard/views/wizard.xml',
        'wizard/views/report_actions.xml',
        'wizard/views/observation_report_action.xml',
        'wizard/views/incident_reporting_report_action.xml',
        'wizard/views/incident_investigation_report_action.xml',
        'wizard/views/capa_summary_report_action.xml',
        'wizard/views/observation_wizard.xml',
        'wizard/views/incident_reporting_wizard.xml',
        'wizard/views/incident_investigation_wizard.xml',
        'wizard/views/capa_wizard.xml',
        'reports/capa_summary_report.xml',
        'reports/incident_investigation_summary_report.xml',
        'reports/incident_reporting_summary_report.xml',
        'reports/observation_summary_report.xml',
        'reports/ra_jsa_summary_report.xml',
        'views/hse_permit_report.xml',
        'views/hse_loto_report.xml',
        'views/hse_hazop_report.xml',
        'views/hse_audit_report.xml',
        'views/hse_compliance_register_report.xml',
        'views/hse_competency_matrix_report.xml',
        'views/hse_equipment_cert_report.xml',
        'views/hse_osha300_log_report.xml',
        'views/hse_monthly_kpi_report.xml',
        'views/summary_menuitems.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
}

