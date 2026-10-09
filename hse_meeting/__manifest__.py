# -*- coding: utf-8 -*-
{
    'name': "hse_meeting",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "SNG",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

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
