# -*- coding: utf-8 -*-
{
    'name': "HSE Client Demo & Comprehensive Data",

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

Includes a restricted client-demo hub at /hse/demo with eight guided
journeys, a 73-area module explorer, ten live report previews, a
downloadable presenter guide and coverage CSV. Additional records cover
HAZOP, LOPA, SIF/SIL, SECE, barrier integrity, process safety events,
SIMOPS radar, specialized permits, environmental and ESG monitoring,
LDAR, chemical SDS, health surveillance, emergency response and contractor
induction. All people, measurements, IDs and contacts are fictional.
Install in an isolated demonstration database only, never production.

All dates are generated relative to install day so status computations
(days-without-LTI, overdue CAPAs, expiring certificates) are meaningful.
    """,

    'author': "HSE Global Enterprise",
    'category': 'Human Resources/HSE',
    'version': '17.0.2.0.0',
    'license': 'LGPL-3',

    'depends': [
        'hse',
        'hse_meeting',
        'hse_reports',
        'observation_portal',
    ],

    'data': [
        'security/demo_security.xml',
        'data/00_master_data.xml',
        'data/10_safety_operations.xml',
        'data/20_actions_compliance.xml',
        'data/30_assets_people.xml',
        'data/90_comprehensive_demo.xml',
        'views/client_demo.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
