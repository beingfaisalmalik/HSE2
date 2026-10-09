# -*- coding: utf-8 -*-
{
    'name': "HSE Enterprise Suite - IBM Maximo HSE Parity",

    'summary': "Complete Health, Safety & Environment (HSE) Enterprise Management Suite",

    'description': """
Complete enterprise Health, Safety and Environment (HSE) management suite matching and exceeding IBM Maximo HSE Manager.
Includes:
- Incident Management & OSHA 300 / API 754 reporting
- Root Cause Analysis (RCFA, 5 Whys, Ishikawa Fishbone, Sequence of Events)
- Permit to Work (PTW / Control of Work) with Atmospheric Gas Testing
- Lock & Tag Out Plans (LOTO) & Zero Energy State Verification
- Management of Change (MOC) with Pre-Start Safety Review (PSSR)
- Non-Conformance Management (NCR) with Quarantine, Disposition & CONC
- Regulatory Compliance & Audit Management (OSHA, EPA, ISO 45001)
- Preparation Activities & Turnaround (TAR) Readiness Gates
- Standard Operating Procedures (SOP) & Execution Steps
- Operating Policies & Workforce Governance Acknowledgments
- Dynamic 5x5 Risk Matrix & Job Safety Analysis (JSA)
- Location Safety Profiles with SECE, Hazardous Zones & Barrier Tracking
- Continuous Improvements (Kaizen / Six Sigma ROI)
- Competency Assurance & Role Qualification Matrix
- Operator's Shift Log & Handover Protocol
- Personnel Certification & License Expiry Tracking
- Centralized Action Tracking (CAPA Engine)
- Benefits & Losses (Production Downtime, Environmental & Safety ROI)
- Equipment Failure Reporting (ISO 14224 Standard)
- Solutions & Lessons Learned Knowledge Base
- Defect Elimination & Bad Actor Resolution (90-Day Run Tracking)
- Safety Bypass Management (Inhibits, Overrides & SIL Criticality)
- Plant Equipment Statutory Certifications (Pressure Vessels, Cranes, PSVs)
- Modern Interactive OWL Executive Dashboard & SCSS Design System
    """,

    'author': "HSE Global Enterprise",
    'website': "https://www.yourcompany.com",
    'category': 'Human Resources/HSE',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'base',
        'mail',
        'hr',
        'website',
        'portal',
        'web',
        'base_tier_validation',
        'base_tier_validation_server_action',
    ],

    # Data files
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'data/ra_jsa_stage_data.xml',
        'data/email_template.xml',
        'data/hse_standard_data.xml',

        # Configuration & Settings
        'views/incident_reporting_settings.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/cancel_wizard.xml',
        'views/review_wizard.xml',
        'views/setting.xml',
        'views/severity_level.xml',
        'views/incident_category.xml',
        'views/incident_member_list.xml',
        'views/injury_create_level.xml',
        'views/investigation_causes.xml',
        'views/req_date_extension.xml',
        'views/hazard_control.xml',
        'views/analysis_form.xml',
        'views/external_team.xml',

        # Core HSE Existing Views
        'views/corrective.xml',
        'views/preventive.xml',
        'views/ra_jsa.xml',
        'views/observation.xml',
        'views/incident_reporting.xml',
        'views/incident_investigation.xml',
        'views/location.xml',
        'views/assets.xml',

        # Advanced IBM Maximo HSE Modules
        'views/hse_risk_matrix_views.xml',
        'views/hse_action_views.xml',
        'views/hse_location_profile_views.xml',
        'views/hse_permit_views.xml',
        'views/hse_loto_views.xml',
        'views/hse_moc_views.xml',
        'views/hse_ncr_views.xml',
        'views/hse_regulatory_compliance_views.xml',
        'views/hse_preparation_activity_views.xml',
        'views/hse_operating_procedure_views.xml',
        'views/hse_operating_policy_views.xml',
        'views/hse_improvement_views.xml',
        'views/hse_competency_views.xml',
        'views/hse_operator_log_views.xml',
        'views/hse_personnel_certification_views.xml',
        'views/hse_equipment_certification_views.xml',
        'views/hse_benefit_loss_views.xml',
        'views/hse_failure_reporting_views.xml',
        'views/hse_solution_views.xml',
        'views/hse_defect_elimination_views.xml',
        'views/hse_bypass_views.xml',
        'views/hse_incident_advanced_views.xml',
        'views/hse_hazop_views.xml',
        'views/hse_lopa_views.xml',
        'views/hse_sece_views.xml',
        'views/hse_process_safety_event_views.xml',
        'views/hse_environmental_views.xml',
        'views/hse_industrial_hygiene_views.xml',
        'views/hse_contractor_views.xml',
        'views/hse_sds_views.xml',
        'views/hse_specialized_permits_views.xml',
        'views/hse_emergency_views.xml',
        'views/hse_audit_views.xml',
        'views/hse_bbs_views.xml',
        'views/hse_sif_views.xml',
        'views/hse_dispersion_views.xml',
        'views/hse_hfacs_views.xml',
        'views/hse_confined_space_views.xml',
        'views/hse_simops_views.xml',
        'views/hse_esg_views.xml',
        'views/hse_health_surveillance_views.xml',
        'views/hse_lifesaving_rules_views.xml',
        'views/hse_process_safety_metrics_views.xml',
        'views/hse_safety_culture_views.xml',
        'views/hse_ldar_views.xml',
        'views/hse_barrier_element_views.xml',
        'views/hse_compliance_calendar_views.xml',
        'views/hse_training_matrix_views.xml',

        # Master Navigation
        'views/hse_menuitems_master.xml',
    ],

    # Assets Bundle for OWL & SCSS
    'assets': {
        'web.assets_backend': [
            'hse/static/src/scss/hse_style.scss',
            'hse/static/src/js/hse_form_enhancer.js',
            'hse/static/src/js/hse_dashboard.js',
            'hse/static/src/js/hse_risk_matrix_widget.js',
            'hse/static/src/js/hse_gas_gauge_widget.js',
            'hse/static/src/js/hse_bowtie_widget.js',
            'hse/static/src/js/hse_dispersion_plume_widget.js',
            'hse/static/src/xml/hse_dashboard.xml',
            'hse/static/src/xml/hse_form_enhancer.xml',
            'hse/static/src/xml/hse_risk_matrix_widget.xml',
            'hse/static/src/xml/hse_gas_gauge_widget.xml',
            'hse/static/src/xml/hse_bowtie_widget.xml',
            'hse/static/src/xml/hse_dispersion_plume_widget.xml',
        ],
    },

    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
