# -*- coding: utf-8 -*-
{
    'name': "observation_portal",

    'summary': "Frontline safety observation portal: photo-enabled hazard reporting and BBS submissions from any browser",

    'description': """
Frontline Safety Observation Portal
-----------------------------------
- Public/portal-friendly observation form with hazard photo upload
- Observations flow into the native HSE observation register for review
- Website templates for submission, confirmation and history views
- Menu visibility restricted to internal HSE users and portal submissions
    """,

    'author': "HSE Global Enterprise",
    'website': "https://www.yourcompany.com",

    'category': 'Human Resources/HSE',
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website', 'portal', 'hse'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/observation_form_template.xml',
        'views/hse_portal_templates.xml',
        'views/observation_menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
}

