# -*- coding: utf-8 -*-
{
    'name': "hse_reports",

    'summary': "Enterprise HSE report suite: incidents/OSHA 300, audits, compliance, competency matrix, statutory certs, monthly KPIs",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

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

