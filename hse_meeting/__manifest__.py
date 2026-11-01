# -*- coding: utf-8 -*-
{
    'name': "hse_meeting",

    'summary': "Safety meetings & toolbox talks: agenda, attendance quorum, corrective actions and printable minutes",

    'description': """
HSE Safety Meeting & Toolbox Talk Management
--------------------------------------------
- Schedule departmental safety meetings, toolbox talks and training sessions
- Track attendance counts with employee-total and quorum validation
- Link meeting type, department and HSE source records
- Generate corrective actions from meeting outcomes
- Printable meeting report / minutes (QWeb)
- Departmental transit wizard for consolidated meeting summaries
    """,

    'author': "HSE Global Enterprise",
    'website': "https://www.yourcompany.com",

    'category': 'Human Resources/HSE',
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr', 'hse'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sequence.xml',
        'views/templates.xml',


        'wizards/transient_wizard_view.xml',
        'reports/report.xml',
        'reports/report_view.xml',
        'views/views.xml',
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
}
