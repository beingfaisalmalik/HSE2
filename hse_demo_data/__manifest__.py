# -*- coding: utf-8 -*-
{
    'name': "HSE Demo Data Loader",

    'summary': "Loads comprehensive, realistic demo data across the entire HSE suite on install",

    'description': """
One-shot sample data loader: install this module after the HSE suite and
every major form ships pre-populated — incidents & OSHA records, safety
observations, permits to work (with gas tests), LOTO isolations, safety
bypasses, stop-work authorities, BBS observations, risk assessments,
MOC, NCR, investigations, CAPA actions, audits & findings, compliance
obligations & tasks, statutory equipment certifications (expired /
expiring / valid), personnel certifications, competency & training-gap
matrices, safety meetings, operator shift log, equipment failure reports,
defect elimination, continuous improvements, operating policies &
procedures (published for the external portal) and API RP 754 exposure
hours that drive the live TRIR KPI.

All dates are generated relative to install day so status computations
(days-without-LTI, overdue CAPAs, expiring certificates) are meaningful.
    """,

    'author': "HSE Global Enterprise",
    'category': 'Human Resources/HSE',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',

    'depends': [
        'hse',
        'hse_meeting',
        'hse_reports',
        'observation_portal',
    ],

    'data': [
        'data/00_master_data.xml',
        'data/10_safety_operations.xml',
        'data/20_actions_compliance.xml',
        'data/30_assets_people.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
