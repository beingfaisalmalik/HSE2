# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.addons.hse.controllers import hse_dashboard_controller


class TestHSEMaximoComprehensive(TransactionCase):
    """
    Comprehensive functional and technical test suite verifying IBM Maximo HSE parity
    and advanced industrial HSE management capabilities across all 24 HSE domains.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Location = cls.env['hse.location.profile']
        cls.Asset = cls.env['assets.form']
        cls.Employee = cls.env['hr.employee']
        cls.User = cls.env.ref('base.user_admin')

        # 1. Master Location Safety Profile
        cls.test_loc = cls.Location.create({
            'name': 'Hydrocracker Unit (HCU-200)',
            'code': 'LOC-HCU-200',
            'location_type': 'unit',
            'hazardous_zone': 'zone1',
            'is_sece': True,
            'sece_classification': 'SECE-BARRIER-01',
            'has_gas_detection': True,
            'has_fire_deluge': True,
            'muster_station_primary': 'Muster Station C - North Boundary',
            'evacuation_route': 'Proceed North to Gate 4 away from prevailing wind',
        })

        # 2. Master Equipment Asset
        cls.test_asset = cls.Asset.create({
            'name': 'P-201A High Pressure Charge Pump',
            'assets_type': 'equipment',
            'location': 'Hydrocracker Unit',
            'description': '12-stage centrifugal pump operating at 180 bar discharge pressure',
            'status': 'active',
        })

        # 3. Master Test Employee
        cls.test_emp = cls.Employee.create({
            'name': 'Marcus Vance',
            'work_email': 'marcus.vance@industry-hse.example',
            'mobile_phone': '+1-555-0199',
        })

    # =========================================================================
    # 1. Incident Management & OSHA 300 Recordkeeping
    # =========================================================================
    def test_01_incident_management_osha(self):
        Incident = self.env['incident.reporting']
        inc = Incident.create({
            'ir_description': 'Acid Gas Scrubber Flange Leak During Startup',
            'incident_type': 'injury',
            'incident_report_date': fields.Datetime.now(),
            'location_profile_id': self.test_loc.id,
            'asset_equipment_id': self.test_asset.id,
            'financial_property_loss': 15000.0,
            'financial_production_loss': 35000.0,
            'process_safety_tier': 'tier2',
            'injury_ids': [(0, 0, {
                'person_type': 'employee',
                'employee_id': self.test_emp.id,
                'injury_severity': 'lost_time',
                'body_part_affected': 'Right Hand',
                'nature_of_injury': 'Chemical Burn',
                'days_away_from_work': 4,
                'days_restricted_duty': 2,
            })],
        })

        self.assertTrue(inc.name, "Incident sequence must be auto-generated")
        self.assertTrue(inc.is_osha_recordable, "Incident should be automatically marked as OSHA 300 recordable")
        self.assertEqual(inc.process_safety_tier, 'tier2')

        # Test workflow transitions
        inc.action_in_process()
        self.assertEqual(inc.state, 'in_process')
        inc.action_in_lock()
        self.assertEqual(inc.state, 'locked')

    # =========================================================================
    # 2. Incident Investigations (RCA, 5 Whys, Timeline)
    # =========================================================================
    def test_02_incident_investigation_rca(self):
        Investigation = self.env['incident.investigation']
        inv = Investigation.create({
            'ref_name': 'INV-2026-HCU-001',
            'summary': 'Detailed Root Cause Analysis of Flange Gasket Failure',
            'investigation_lead': self.test_emp.id,
            'rca_method': 'five_whys',
            'immediate_cause': 'Gasket extruded under high process pressure',
            'underlying_cause': 'Torque sequence was not followed during maintenance turnaround',
            'root_cause': 'Absence of mandatory bolt tensioning QA verification step',
            'why_ids': [
                (0, 0, {'why_number': 1, 'question': 'Why did the flange leak?', 'answer': 'Gasket extruded under pressure'}),
                (0, 0, {'why_number': 2, 'question': 'Why did the gasket extrude?', 'answer': 'Uneven stud bolt tensioning'}),
                (0, 0, {'why_number': 3, 'question': 'Why was tension uneven?', 'answer': 'Manual criss-cross pattern was skipped'}),
                (0, 0, {'why_number': 4, 'question': 'Why was it skipped?', 'answer': 'Contractor lacked hydraulic bolt tensioner'}),
                (0, 0, {'why_number': 5, 'question': 'Why was tooling missing?', 'answer': 'Turnaround job packet lacked tooling checklist', 'is_root_cause': True}),
            ],
        })

        self.assertTrue(inv.name, "Investigation reference should be generated")
        self.assertEqual(len(inv.why_ids), 5, "5 Whys analysis should contain 5 structured steps")
        inv.action_in_process()
        self.assertEqual(inv.state, 'in_process')

    # =========================================================================
    # 3. Management of Change (MOC) & PSSR
    # =========================================================================
    def test_03_management_of_change(self):
        MOC = self.env['hse.moc']
        moc = MOC.create({
            'title': 'Install High Integrity Pressure Protection System (HIPPS) on Feed Line',
            'change_type': 'permanent',
            'category': 'instrumentation',
            'location_id': self.test_loc.id,
            'asset_id': self.test_asset.id,
            'description_of_change': 'Upgrade from conventional relief valve to SIL-3 dual 2oo3 HIPPS valves',
            'justification': 'Eliminate flare system bottleneck during emergency overpressure events',
            'initial_risk_score': 16,
            'residual_risk_score': 3,
            'estimated_cost': 125000.0,
            'pssr_required': True,
        })

        self.assertTrue(moc.name, "MOC sequential code must be auto-generated")
        self.assertEqual(moc.state, 'draft')

        # Lifecycle: draft -> technical_review -> approved -> pssr -> implementation -> commissioned -> closed
        moc.action_submit_review()
        self.assertEqual(moc.state, 'technical_review')
        moc.action_approve()
        self.assertEqual(moc.state, 'approved')
        moc.action_start_pssr()
        self.assertEqual(moc.state, 'pssr')
        moc.action_start_implementation()
        self.assertEqual(moc.state, 'implementation')
        moc.action_commission()
        self.assertEqual(moc.state, 'commissioned')
        moc.action_close()
        self.assertEqual(moc.state, 'closed')

    # =========================================================================
    # 4. Non-Conformance Management (NCR) & Material Quarantine
    # =========================================================================
    def test_04_non_conformance_ncr(self):
        NCR = self.env['hse.ncr']
        ncr = NCR.create({
            'title': 'Incorrect Gasket Metallurgy Supplied for Sulfuric Acid Service',
            'ncr_source': 'inspection',
            'severity': 'critical',
            'location_id': self.test_loc.id,
            'problem_description': 'Spiral wound gaskets delivered with carbon steel windings instead of Alloy 20',
            'specification_requirement': 'ASME B16.20 Alloy 20 / PTFE for Class 300 Acid Lines',
            'is_quarantined': True,
            'quarantine_tag_no': 'QUAR-TAG-2026-99',
            'quarantine_location': 'Warehouse Hazardous Cage 2',
            'disposition': 'rtv',
            'conc_material_cost': 4500.0,
            'conc_labor_cost': 600.0,
            'conc_delay_penalty': 900.0,
        })

        self.assertTrue(ncr.name, "NCR code must be generated")
        self.assertEqual(ncr.conc_total, 6000.0, "Total consequence cost should equal 4500 + 600 + 900 = 6000")

        # Lifecycle
        ncr.action_quarantine()
        self.assertEqual(ncr.state, 'quarantined')
        ncr.action_request_disposition()
        self.assertEqual(ncr.state, 'disposition_review')
        ncr.action_approve_disposition()
        self.assertEqual(ncr.state, 'disposition_approved')
        ncr.action_close()
        self.assertEqual(ncr.state, 'closed')

    # =========================================================================
    # 5. Regulatory Compliance & Auditing
    # =========================================================================
    def test_05_regulatory_compliance(self):
        Regulation = self.env['hse.regulation']
        Audit = self.env['hse.compliance.audit']

        reg = Regulation.create({
            'name': 'API RP 754 Process Safety Indicators for Refining & Petrochemical Industries',
            'code': 'API-RP-754',
            'regulatory_body': 'American Petroleum Institute (API)',
            'jurisdiction': 'Global Industry Standard',
            'category': 'process_safety',
            'summary': 'Standardized tracking of Tier 1 and Tier 2 Process Safety Events (PSE)',
        })

        self.assertEqual(reg.state, 'active')

        audit = Audit.create({
            'title': 'Annual Q3 Process Safety Performance Verification',
            'regulation_id': reg.id,
            'location_id': self.test_loc.id,
            'audit_date': date.today(),
            'findings_count': 2,
            'score_percentage': 96.5,
        })

        self.assertTrue(audit.name)
        audit.action_start()
        self.assertEqual(audit.state, 'in_progress')
        audit.action_complete()
        self.assertEqual(audit.state, 'completed')
        audit.action_close()
        self.assertEqual(audit.state, 'closed')

    # =========================================================================
    # 6. Preparation Activities (Gate Readiness)
    # =========================================================================
    def test_06_preparation_activities(self):
        Prep = self.env['hse.preparation.activity']
        prep = Prep.create({
            'title': 'Vessel Blind List Verification and Nitrogen Gas Freeing',
            'activity_type': 'confined_prep',
            'scheduled_date': fields.Date.today(),
            'location_id': self.test_loc.id,
            'asset_id': self.test_asset.id,
            'gate1_planning': True,
            'gate2_isolation': True,
            'gate3_site_prep': True,
            'gate4_ready': True,
        })

        self.assertTrue(prep.name)
        prep.action_start_prep()
        self.assertEqual(prep.state, 'in_prep')
        prep.action_authorize_ready()
        self.assertEqual(prep.state, 'ready')
        prep.action_complete()
        self.assertEqual(prep.state, 'completed')

    # =========================================================================
    # 7. Operating Procedures (SOP)
    # =========================================================================
    def test_07_operating_procedures(self):
        SOP = self.env['hse.operating.procedure']
        sop = SOP.create({
            'name': 'Emergency Reactor Depressuring and Quench Gas Injection',
            'procedure_code': 'SOP-HCU-EMERG-004',
            'procedure_type': 'emergency',
            'revision': 'Rev 4.1',
            'effective_date': date.today(),
            'purpose_and_scope': 'Depressurize reactor from 160 bar to 25 bar within 15 minutes during runaway exotherm',
            'is_safety_critical': True,
        })

        self.assertEqual(sop.state, 'draft')
        sop.action_submit_review()
        self.assertEqual(sop.state, 'review')
        sop.action_approve()
        self.assertEqual(sop.state, 'approved')
        sop.action_publish()
        self.assertEqual(sop.state, 'published')

    # =========================================================================
    # 8. Operating Policies
    # =========================================================================
    def test_08_operating_policies(self):
        Policy = self.env['hse.operating.policy']
        pol = Policy.create({
            'name': 'Mandatory Stop Work Authority (SWA) Protocol',
            'policy_code': 'POL-HSE-SWA-2026',
            'policy_type': 'stop_work',
            'core_principles': 'Zero Harm, Stop Work Authority, Complete Barrier Integrity',
            'mandatory_rules': 'Immediate shutdown upon hydrocarbon detection; full PPE compliance',
            'effective_date': date.today(),
            'policy_statement': '<p>Empower all workforce members to immediately halt operations when unsafe conditions arise.</p>',
        })

        self.assertEqual(pol.state, 'draft')
        pol.action_approve()
        self.assertEqual(pol.state, 'approved')

    # =========================================================================
    # 9. Risk Assessment (RA / JSA)
    # =========================================================================
    def test_09_risk_assessment_jsa(self):
        RA = self.env['ra_jsa.model']
        Hazard = self.env['ra_jsa.hazard']

        ra = RA.create({
            'description': 'Hot Work Replacement of Catalytic Reactor Flare Header Valve',
            'type': 'risk_assessment',
            'priority': 'high',
        })

        self.assertTrue(ra.name)

        hazard = Hazard.create({
            'ra_id': ra.id,
            'likelihood': '5',
            'severity_level': '5',
            'post_likelihood': '1',
            'post_severity_level': '2',
        })

        # Initial risk: 5 x 5 = 25 -> High
        self.assertEqual(hazard.risk_level, 'High')
        # Residual risk: 1 x 2 = 2 -> Low
        self.assertEqual(hazard.risk_level_, 'Low')

    # =========================================================================
    # 10. Interactive 5x5 Risk Matrix
    # =========================================================================
    def test_10_risk_matrix(self):
        Matrix = self.env['hse.risk.matrix']
        Cell = self.env['hse.risk.matrix.cell']

        matrix = Matrix.create({
            'name': 'Corporate 5x5 Quantitative Risk Matrix',
            'dimension': '5x5',
            'description': 'Standard 5x5 likelihood x consequence risk evaluation framework',
        })

        cell = Cell.create({
            'matrix_id': matrix.id,
            'likelihood_level': 5,
            'consequence_level': 5,
            'risk_level': 'critical',
            'color': '#e11d48',
        })

        self.assertEqual(cell.risk_score, 25)
        self.assertEqual(cell.risk_level, 'critical')

    # =========================================================================
    # 11. Location Safety Profile & Barrier Metrics
    # =========================================================================
    def test_11_location_profile(self):
        loc = self.Location.create({
            'name': 'Fluid Catalytic Cracking Unit (FCCU-300)',
            'code': 'LOC-FCCU-300',
            'location_type': 'unit',
            'hazardous_zone': 'zone0',
            'is_sece': True,
        })

        # Stat button actions
        res_permits = loc.action_view_permits()
        self.assertEqual(res_permits['res_model'], 'hse.permit')

        res_incidents = loc.action_view_incidents()
        self.assertEqual(res_incidents['res_model'], 'incident.reporting')

        res_loto = loc.action_view_loto()
        self.assertEqual(res_loto['res_model'], 'hse.loto.plan')

        res_bypasses = loc.action_view_bypasses()
        self.assertEqual(res_bypasses['res_model'], 'hse.bypass')

    # =========================================================================
    # 12. Continuous Improvement (CI / Kaizen)
    # =========================================================================
    def test_12_continuous_improvement(self):
        CI = self.env['hse.improvement']
        ci = CI.create({
            'title': 'Automate Gas Flare Purge Rate with Closed-Loop Nitrogen Optimizer',
            'initiative_type': 'kaizen',
            'category': 'safety',
            'location_id': self.test_loc.id,
            'current_state': 'Manual bypass tracking process prone to delays',
            'proposed_solution': 'Automated bypass logging and SMS notification',
            'implementation_budget': 24000.0,
            'estimated_annual_savings': 96000.0,
        })

        self.assertTrue(ci.name)
        self.assertEqual(ci.state, 'submitted')

    # =========================================================================
    # 13. Competency Management
    # =========================================================================
    def test_13_competency_management(self):
        Competency = self.env['hse.competency']
        EmpComp = self.env['hse.employee.competency']

        comp = Competency.create({
            'name': 'Confined Space Entry Supervisor',
            'code': 'COMP-CS-001',
            'category': 'control_of_work',
            'description': 'Qualification for confined space supervisor role',
            'validity_months': 24,
            'mandatory_for_permits': True,
        })

        emp_comp = EmpComp.create({
            'employee_id': self.test_emp.id,
            'competency_id': comp.id,
            'proficiency_level': 'level4',
            'state': 'active',
            'assessment_date': date.today(),
            'expiry_date': date.today() + timedelta(days=730),
        })

        self.assertEqual(emp_comp.state, 'active')

    # =========================================================================
    # 14. Operators Log (Shift Handovers)
    # =========================================================================
    def test_14_operators_log(self):
        OpLog = self.env['hse.operator.log']
        Entry = self.env['hse.operator.log.entry']

        log = OpLog.create({
            'location_id': self.test_loc.id,
            'shift_type': 'day',
            'operating_status': 'normal',
            'production_output': '48,500 BPD High Purity Gasoline',
        })

        self.assertTrue(log.name)
        self.assertEqual(log.state, 'open')

        entry = Entry.create({
            'log_id': log.id,
            'category': 'routine',
            'priority': 'high',
            'description': 'Quarterly safety shower and eye wash station testing completed with zero faults',
        })

        self.assertTrue(entry.id)
        log.action_initiate_handover()
        self.assertEqual(log.state, 'handover_review')
        log.relieving_operator_id = self.User.id
        log.action_accept_handover()
        self.assertEqual(log.state, 'relieved')

    # =========================================================================
    # 15. Personnel Certification Tracking
    # =========================================================================
    def test_15_personnel_certification(self):
        Cert = self.env['hse.personnel.certification']
        cert = Cert.create({
            'employee_id': self.test_emp.id,
            'certification_name': 'OPITO BOSIET with EBS and Travel Safely by Boat',
            'certification_type': 'bosiet',
            'certificate_number': 'OPITO-BOSIET-99412',
            'issuing_body': 'Offshore Petroleum Industry Training Org',
            'issue_date': date.today() - timedelta(days=100),
            'expiry_date': date.today() + timedelta(days=630),
            'state': 'valid',
        })

        self.assertTrue(cert.name)
        self.assertEqual(cert.state, 'valid')
        self.assertFalse(cert.is_expired)

    # =========================================================================
    # 16. Action Tracking (Universal CAPA Engine)
    # =========================================================================
    def test_16_action_tracking(self):
        Action = self.env['hse.action']
        act = Action.create({
            'title': 'Install Nitrogen Purge Check Valve on Reactor Feed System',
            'description': 'Install new check valve to prevent backflow into nitrogen header',
            'action_type': 'corrective',
            'source_type': 'investigation',
            'source_reference': 'INV-2026-004',
            'priority': '1',
            'target_date': date.today() + timedelta(days=14),
            'progress': 0,
        })

        self.assertTrue(act.name)
        self.assertEqual(act.state, 'draft')

        act.action_assign()
        self.assertEqual(act.state, 'assigned')

        act.action_start()
        self.assertEqual(act.state, 'in_progress')

        act.progress = 100
        act.action_implement()
        self.assertEqual(act.state, 'implemented')

        act.verification_status = 'effective'
        act.action_verify()
        self.assertEqual(act.state, 'verified')

    # =========================================================================
    # 17. Benefits & Losses (HSE Financial Impact Accounting)
    # =========================================================================
    def test_17_benefits_losses(self):
        BenefitLoss = self.env['hse.benefit.loss']
        bl = BenefitLoss.create({
            'title': 'Loss Event: Flange Rupture on Reformer Desulfurization Train',
            'event_type': 'loss',
            'event_date': date.today(),
            'location_id': self.test_loc.id,
            'asset_id': self.test_asset.id,
            'loss_equipment_repair': 15000.0,
            'loss_production_cost': 35000.0,
            'loss_environmental_cleanup': 8000.0,
            'loss_regulatory_fines': 25000.0,
        })

        self.assertTrue(bl.name)
        self.assertAlmostEqual(bl.total_loss, 83000.0)
        self.assertEqual(bl.state, 'draft')

    # =========================================================================
    # 18. Lockout / Tagout (LOTO) Energy Isolation
    # =========================================================================
    def test_18_loto_energy_isolation(self):
        Plan = self.env['hse.loto.plan']
        Point = self.env['hse.loto.point']

        plan = Plan.create({
            'title': 'Positive Mechanical & Electrical Isolation of Reactor Feed Pump',
            'location_id': self.test_loc.id,
            'asset_id': self.test_asset.id,
            'system_description': 'Suction, discharge, minimum flow, and 4160V electric motor breaker',
            'energy_electrical': True,
            'energy_hydraulic': True,
            'energy_mechanical': True,
            'zero_energy_method': 'combination',
            'master_lockbox_no': 'LB-HCU-101',
        })

        self.assertTrue(plan.name)
        self.assertEqual(plan.state, 'draft')

        p1 = Point.create({
            'plan_id': plan.id,
            'sequence': 10,
            'point_identifier': 'BKR-4160-HCU-12',
            'isolation_type': 'breaker_open',
            'lock_number': 'LOTO-RED-001',
            'tag_number': 'TAG-DANGER-1001',
            'applied_by': 'Robert Taylor (Lead Electrician)',
        })

        p2 = Point.create({
            'plan_id': plan.id,
            'sequence': 20,
            'point_identifier': 'V-HCU-SUC-01',
            'isolation_type': 'blind_installed',
            'lock_number': 'LOTO-BLUE-002',
            'tag_number': 'TAG-DANGER-1002',
            'applied_by': 'David Chen (Process Operator)',
        })

        self.assertEqual(len(plan.point_ids), 2)
        plan.zero_energy_verified = True

        plan.action_approve()
        self.assertEqual(plan.state, 'approved')
        plan.action_isolate()
        self.assertEqual(plan.state, 'isolated')
        
        # De-isolate after verifying all three safety conditions
        plan.deisolate_tools_cleared = True
        plan.deisolate_guards_replaced = True
        plan.deisolate_personnel_clear = True
        plan.action_deisolate()
        self.assertEqual(plan.state, 'de-isolated')

    # =========================================================================
    # 19. Failure Reporting (ISO 14224 FRACAS Standard)
    # =========================================================================
    def test_19_failure_reporting_iso14224(self):
        FRACAS = self.env['hse.failure.report']
        fr = FRACAS.create({
            'asset_id': self.test_asset.id,
            'location_id': self.test_loc.id,
            'equipment_class': 'pump',
            'failed_component': 'Radial Thrust Bearing (SKF Angular Contact)',
            'failure_mode': 'vib_high',
            'failure_mechanism': 'wear',
            'failure_cause': 'lubrication',
            'detection_method': 'alarm',
            'impact_level': 'standby_switch',
            'downtime_hours': 3.5,
            'repair_time_hours': 8.0,
            'remedial_action_taken': 'Flushed bearing housing, replaced worn bearing set, aligned motor shaft',
        })

        self.assertTrue(fr.name)
        self.assertEqual(fr.state, 'reported')
        fr.action_analyze()
        self.assertEqual(fr.state, 'under_analysis')
        fr.action_repaired()
        self.assertEqual(fr.state, 'repaired')
        fr.action_close()
        self.assertEqual(fr.state, 'closed')

    # =========================================================================
    # 20. Solutions & Lessons Learned Knowledge Base
    # =========================================================================
    def test_20_solutions_knowledge_base(self):
        Solution = self.env['hse.solution']
        sol = Solution.create({
            'name': 'API 682 Plan 53B Pressurized Barrier Fluid System Retrofit',
            'category': 'mechanical',
            'applicable_equipment': 'pumps',
            'problem_symptoms': 'Chronic seal face vapor lock on condensate transfer pumps',
            'root_cause_addressed': 'Fluid flashing at atmospheric barrier pressure',
            'detailed_solution': '<p>Install pressurized bladder accumulator maintained at 2.5 bar over stuffing box.</p>',
            'estimated_annual_cost_avoidance': 65000.0,
        })

        self.assertTrue(sol.name)
        self.assertEqual(sol.state, 'draft')
        sol.action_publish()
        self.assertEqual(sol.state, 'published')

    # =========================================================================
    # 21. Defect Elimination (Chronic Failure Program)
    # =========================================================================
    def test_21_defect_elimination(self):
        DE = self.env['hse.defect.elimination']
        de = DE.create({
            'title': 'Eliminate Chronic Thermal Fatigue in Heat Exchanger E-201 Channel Head',
            'asset_id': self.test_asset.id,
            'location_id': self.test_loc.id,
            'defect_category': 'vibration_resonance',
            'underlying_cause': 'Thermal stress cycling at weld boundary',
            'failures_last_12_months': 4,
            'annual_maintenance_spend': 32000.0,
            'annual_production_loss': 85000.0,
            'defect_description': 'Cyclic thermal shock causing weld ligament cracking every 3 months',
            'elimination_strategy': 'Install automated ramp rate limiter on feed bypass control loop',
        })

        self.assertTrue(de.name)
        self.assertEqual(de.state, 'identified')
        de.action_start_team_review()
        self.assertEqual(de.state, 'team_review')
        de.action_execute()
        self.assertEqual(de.state, 'action_execution')
        de.action_start_tracking()
        self.assertEqual(de.state, 'tracking_period')
        de.action_mark_eliminated()
        self.assertEqual(de.state, 'eliminated')
        de.action_close()
        self.assertEqual(de.state, 'closed')

    # =========================================================================
    # 22. Safety Bypass / Inhibit Management (SECE Barrier Protection)
    # =========================================================================
    def test_22_safety_bypass_management(self):
        Bypass = self.env['hse.bypass']
        byp = Bypass.create({
            'title': 'Temporary Trip Inhibit for Reformer Combustible Gas Detector GD-201',
            'tag_number': 'GD-201A',
            'location_id': self.test_loc.id,
            'asset_id': self.test_asset.id,
            'bypass_type': 'fire_gas',
            'safety_criticality': 'sil2',
            'reason': 'calibration',
            'details': 'Transmitter sensor head recalibration and proof test',
            'compensating_controls': 'Continuous manual combustible LEL perimeter survey every 30 minutes',
            'has_dedicated_watcher': True,
            'expected_duration_hours': 4.0,
        })

        self.assertTrue(byp.name)
        self.assertEqual(byp.state, 'draft')
        byp.action_request()
        self.assertEqual(byp.state, 'requested')
        byp.action_approve()
        self.assertEqual(byp.state, 'approved')
        byp.action_apply_bypass()
        self.assertEqual(byp.state, 'active')
        byp.reinstatement_tested = True
        byp.action_reinstate()
        self.assertEqual(byp.state, 'reinstated')

    # =========================================================================
    # 23. Equipment Certification Tracking
    # =========================================================================
    def test_23_equipment_certification(self):
        Cert = self.env['hse.equipment.certification']
        cert = Cert.create({
            'certificate_number': 'CERT-NB-ASME-2026-081',
            'title': 'National Board Boiler & Pressure Vessel Statutory Hydrostatic Verification',
            'asset_id': self.test_asset.id,
            'location_id': self.test_loc.id,
            'cert_type': 'pressure_vessel',
            'certifying_authority': 'Bureau Veritas Industrial Inspections',
            'design_pressure_psi': 2600.0,
            'test_pressure_psi': 3900.0,
            'issue_date': date.today() - timedelta(days=60),
            'expiry_date': date.today() + timedelta(days=670),
            'state': 'valid',
        })

        self.assertTrue(cert.name)
        self.assertEqual(cert.state, 'valid')
        self.assertFalse(cert.is_expired)

    # =========================================================================
    # 24. Permit to Work (PTW) & Multi-Gas Atmospheric Testing
    # =========================================================================
    def test_24_permit_to_work_and_gas_testing(self):
        Permit = self.env['hse.permit']
        GasTest = self.env['hse.permit.gas.test']

        permit = Permit.create({
            'title': 'Confined Space Entry and Tray Inspection Inside Reactor V-201',
            'permit_type': 'confined_space',
            'location_id': self.test_loc.id,
            'asset_id': self.test_asset.id,
            'work_order_ref': 'WO-2026-9014',
            'performing_company': 'internal',
            'receiver_name': 'Marcus Vance',
            'workers_count': 3,
            'hazard_toxic': True,
            'hazard_oxygen_deficiency': True,
            'req_gas_test': True,
            'req_hole_watch': True,
            'req_breathing_apparatus': True,
        })

        self.assertTrue(permit.name)
        self.assertEqual(permit.state, 'draft')

        # Add atmospheric gas test result
        gt = GasTest.create({
            'permit_id': permit.id,
            'tester_name': 'Marcus Vance (Certified AGT)',
            'tester_certification_no': 'AGT-CERT-0092',
            'oxygen_percent': 20.9,
            'lel_percent': 0.0,
            'h2s_ppm': 0.0,
            'co_ppm': 1.5,
            'is_safe_to_work': True,
        })

        self.assertTrue(gt.is_safe_to_work)
        self.assertEqual(len(permit.gas_test_ids), 1)

        # Full lifecycle: draft -> requested -> reviewed -> approved -> active -> suspended -> active -> handback -> closed
        permit.action_submit()
        self.assertEqual(permit.state, 'requested')
        permit.action_review()
        self.assertEqual(permit.state, 'reviewed')
        permit.action_approve()
        self.assertEqual(permit.state, 'approved')
        permit.action_start_work()
        self.assertEqual(permit.state, 'active')
        permit.action_suspend()
        self.assertEqual(permit.state, 'suspended')
        permit.action_start_work()
        self.assertEqual(permit.state, 'active')
        permit.action_handback()
        self.assertEqual(permit.state, 'handback')
        permit.action_close()
        self.assertEqual(permit.state, 'closed')

    # =========================================================================
    # 25. Modern Executive Dashboard Controller API Test
    # =========================================================================
    def test_25_dashboard_controller_kpi(self):
        controller = hse_dashboard_controller.HSEDashboardController()
        mock_req = MagicMock()
        mock_req.env = self.env
        with patch.object(hse_dashboard_controller, 'request', mock_req):
            response = controller._collect_dashboard_data()
            self.assertIn('active_permits', response)
            self.assertIn('active_bypasses', response)
            self.assertIn('active_loto', response)
            self.assertIn('total_incidents', response)
            self.assertIn('active_permits_list', response)
            self.assertIn('active_bypasses_list', response)
            self.assertIn('matrix_grid', response)
            self.assertIn('simops_conflicts_count', response)
            self.assertIn('barrier_health_pct', response)
            self.assertIn('days_without_lti', response)

    # =========================================================================
    # 26. SIMOPS (Simultaneous Operations) Collision Detector
    # =========================================================================
    def test_26_simops_collision_detection(self):
        Permit = self.env['hse.permit']
        
        # Create Permit A: Hot Work in Crude Unit
        permit_a = Permit.create({
            'title': 'Hot Welding on Header 14-FL-08',
            'permit_type': 'hot_work',
            'location_id': self.test_loc.id,
            'requester_id': self.User.id,
            'start_datetime': datetime.now() - timedelta(hours=1),
            'end_datetime': datetime.now() + timedelta(hours=10),
            'state': 'active',
        })

        # Create Permit B: Confined Space Entry in same Crude Unit with overlapping window
        permit_b = Permit.create({
            'title': 'Confined Space Cleaning inside Separator V-101',
            'permit_type': 'confined_space',
            'location_id': self.test_loc.id,
            'requester_id': self.User.id,
            'start_datetime': datetime.now(),
            'end_datetime': datetime.now() + timedelta(hours=8),
            'state': 'approved',
        })

        # Force recomputation of SIMOPS
        permit_b._compute_simops()
        self.assertTrue(permit_b.has_simops_conflict)
        self.assertEqual(permit_b.simops_risk_level, 'high')
        self.assertIn(permit_a, permit_b.conflicting_permit_ids)

        # Attempt to start work without SIMOPS coordinator authorization should raise UserError
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            permit_b.action_start_work()

        # Authorize SIMOPS
        permit_b.simops_authorized_by = self.User.id
        permit_b.simops_mitigation = 'Physical 50m barrier installed; gas monitoring continuous; coordinator stationed.'
        permit_b.action_start_work()
        self.assertEqual(permit_b.state, 'active')

    # =========================================================================
    # 27. Bow-Tie Safety Barrier Analysis
    # =========================================================================
    def test_27_bowtie_barrier_analysis(self):
        Investigation = self.env['incident.investigation']
        Bowtie = self.env['hse.bowtie.barrier']

        inv = Investigation.create({
            'ref_name': 'INV-BOWTIE-001',
            'summary': 'Process Line Overpressure Investigation',
            'immediate_cause': 'Control valve failure',
            'underlying_cause': 'Scale buildup',
            'root_cause': 'Instrument maintenance interval too long',
            'rca_method': 'comprehensive',
        })

        # Add Preventive Barrier (Left side of Bow-Tie: Threat -> Top Event)
        p_barrier = Bowtie.create({
            'investigation_id': inv.id,
            'side': 'preventive',
            'barrier_category': 'engineered_active',
            'threat_or_consequence': 'Control Valve Failure / Overpressure',
            'barrier_name': 'High Pressure Alarm & Automatic Trip PSHH-104',
            'barrier_status': 'failed',
            'failure_mechanism': 'Transmitter sensing port plugged with scale',
        })

        # Add Mitigative Barrier (Right side of Bow-Tie: Top Event -> Consequence)
        m_barrier = Bowtie.create({
            'investigation_id': inv.id,
            'side': 'mitigative',
            'barrier_category': 'engineered_active',
            'threat_or_consequence': 'Vessel Rupture / Hydrocarbon Cloud',
            'barrier_name': 'Safety Relief Valve PSV-104 Lift to Flare',
            'barrier_status': 'effective',
        })

        self.assertEqual(len(inv.bowtie_barrier_ids), 2)
        self.assertEqual(p_barrier.barrier_status, 'failed')
        self.assertEqual(m_barrier.barrier_status, 'effective')

    # =========================================================================
    # 28. Management of Change (MOC) PSSR Standard Checklist Population
    # =========================================================================
    def test_28_moc_pssr_standard_checklist(self):
        Moc = self.env['hse.moc']
        moc = Moc.create({
            'title': 'Upgrade Suction Strainer to Duplex Filter Scheme',
            'change_type': 'permanent',
            'category': 'equipment',
            'location_id': self.test_loc.id,
            'description_of_change': 'Install parallel basket strainer to allow online cleaning without shutdown',
            'justification': 'Eliminate pump cavitation trips during heavy feedstock runs',
            'pssr_required': True,
        })

        self.assertEqual(len(moc.pssr_line_ids), 0)
        # Populate standard PSSR items
        moc.action_load_default_pssr()
        self.assertGreaterEqual(len(moc.pssr_line_ids), 8)
        self.assertFalse(moc.pssr_completed)

        # Mark all items verified
        for line in moc.pssr_line_ids:
            line.is_verified = True
        moc._compute_pssr_status()
        self.assertTrue(moc.pssr_completed)

    # =========================================================================
    # 29. Location Chemical Inventory & NFPA 704
    # =========================================================================
    def test_29_chemical_inventory_nfPA(self):
        Chemical = self.env['hse.location.chemical']
        chem = Chemical.create({
            'location_id': self.test_loc.id,
            'chemical_name': 'Hydrogen Sulfide (H₂S)',
            'cas_number': '7783-06-4',
            'physical_state': 'gas',
            'nfpa_health': 4,
            'nfpa_flammability': 4,
            'nfpa_instability': 0,
            'quantity_stored': 250.0,
            'unit_of_measure': 'kg',
            'ghs_toxic': True,
            'ghs_flammable': True,
        })

        self.assertEqual(chem.nfpa_health, 4)
        self.assertEqual(chem.chemical_name, 'Hydrogen Sulfide (H₂S)')
        self.test_loc._compute_chemical_count()
        self.assertGreaterEqual(self.test_loc.chemical_count, 1)

    # =========================================================================
    # 30. Lockout / Tagout (LOTO) De-isolation Safety Enforcement
    # =========================================================================
    def test_30_loto_deisolation_safety_checks(self):
        from odoo.exceptions import UserError
        Loto = self.env['hse.loto.plan']
        Point = self.env['hse.loto.point']

        plan = Loto.create({
            'title': 'Turbine Feed Pump P-201 Motor Overhaul',
            'location_id': self.test_loc.id,
            'system_description': 'Motor 4160V feeder and suction/discharge block valves',
            'energy_electrical': True,
            'zero_energy_method': 'multimeter',
            'zero_energy_verified': True,
            'zero_energy_verified_by': self.User.id,
        })
        plan.action_approve()
        plan.action_isolate()
        self.assertEqual(plan.state, 'isolated')

        # De-isolation without safety checks must raise UserError
        with self.assertRaises(UserError):
            plan.action_deisolate()

        # Fulfill all safety conditions
        plan.deisolate_tools_cleared = True
        plan.deisolate_guards_replaced = True
        plan.deisolate_personnel_clear = True
        plan.action_deisolate()
        self.assertEqual(plan.state, 'de-isolated')

    # =========================================================================
    # 31. Operator Log Standing / Defeated Alarms (ISA 18.2)
    # =========================================================================
    def test_31_standing_alarms_in_shift_log(self):
        OperatorLog = self.env['hse.operator.log']
        Alarm = self.env['hse.operator.log.alarm']

        log = OperatorLog.create({
            'shift_type': 'night',
            'location_id': self.test_loc.id,
            'operating_status': 'normal',
            'handover_standing_orders': 'Night shift process operations overview CDU-100',
        })

        alarm = Alarm.create({
            'log_id': log.id,
            'tag_number': 'TAHH-104B',
            'description': 'Atmospheric Tower Top Tray High-High Temperature Trip',
            'priority': 'critical',
            'status': 'defeated',
            'reason': 'Thermowell RTD sensor failure producing spurious spikes',
            'compensating_measure': 'Continuous local thermometer monitoring every 30 mins',
        })

        self.assertEqual(alarm.status, 'defeated')
        self.assertEqual(alarm.priority, 'critical')
        self.assertEqual(len(log.alarm_ids), 1)

    # =========================================================================
    # 32. Multi-Gas Atmospheric Telemetry & Verification
    # =========================================================================
    def test_32_permit_gas_test_telemetry(self):
        Permit = self.env['hse.permit']
        GasTest = self.env['hse.permit.gas.test']

        permit = Permit.create({
            'title': 'Confined Space Inspection Inside Column C-102',
            'permit_type': 'confined_space',
            'location_id': self.test_loc.id,
            'requester_id': self.User.id,
            'req_gas_test': True,
        })

        # Test Safe Gas Sample
        test_safe = GasTest.create({
            'permit_id': permit.id,
            'test_time': fields.Datetime.now(),
            'tester_name': 'Michael Davies (AGT-01)',
            'oxygen_percent': 20.9,
            'lel_percent': 0.0,
            'h2s_ppm': 0.0,
            'co_ppm': 2.0,
            'instrument_serial_no': 'Industrial Scientific Ventis MX4 #S/N 26-9901',
        })
        self.assertTrue(test_safe.is_safe_to_work)
        self.assertEqual(test_safe.oxygen_percent, 20.9)

        # Test Unsafe Gas Sample (High H2S & LEL)
        test_unsafe = GasTest.create({
            'permit_id': permit.id,
            'test_time': fields.Datetime.now(),
            'tester_name': 'Michael Davies (AGT-01)',
            'oxygen_percent': 20.5,
            'lel_percent': 15.0, # Dangerous LEL
            'h2s_ppm': 25.0, # Dangerous H2S
            'co_ppm': 10.0,
            'toxic_gas_name': 'SO2',
            'toxic_gas_ppm': 12.0,
        })
        self.assertFalse(test_unsafe.is_safe_to_work)
        self.assertGreater(test_unsafe.h2s_ppm, 5.0)

    # =========================================================================
    # 33. Risk Matrix 5x5 Severity / Likelihood ALARP Evaluation
    # =========================================================================
    def test_33_risk_matrix_5x5_levels(self):
        res_extreme = self.env['hse.risk.matrix'].calculate_risk(5, 5)
        self.assertEqual(res_extreme['score'], 25)
        self.assertEqual(res_extreme['level'], 'critical')

        res_low = self.env['hse.risk.matrix'].calculate_risk(1, 1)
        self.assertEqual(res_low['score'], 1)
        self.assertEqual(res_low['level'], 'low')

        res_med = self.env['hse.risk.matrix'].calculate_risk(3, 2)
        self.assertEqual(res_med['score'], 6)
        self.assertEqual(res_med['level'], 'medium')

    # =========================================================================
    # 34. Bypass / Override Management Workflow
    # =========================================================================
    def test_34_bypass_override_management(self):
        Bypass = self.env['hse.bypass']
        bypass = Bypass.create({
            'title': 'Bypass of Level Switch LSHH-101 on Separator V-102',
            'bypass_type': 'sis',
            'location_id': self.test_loc.id,
            'tag_number': 'LSHH-101',
            'reason': 'fault',
            'details': 'Replacement of float assembly damaged during startup',
            'compensating_controls': 'Manual operator stationed at gauge glass with dedicated UHF radio',
            'safety_criticality': 'sil2',
            'expected_duration_hours': 12.0,
        })
        self.assertEqual(bypass.state, 'draft')
        bypass.action_request()
        self.assertEqual(bypass.state, 'requested')
        bypass.action_approve()
        self.assertEqual(bypass.state, 'approved')
        bypass.action_apply_bypass()
        self.assertEqual(bypass.state, 'active')
        bypass.reinstatement_tested = True
        bypass.action_reinstate()
        self.assertEqual(bypass.state, 'reinstated')

    # =========================================================================
    # 35. QWeb PDF Report Generation & Rendering Check
    # =========================================================================
    def test_35_qweb_reports_rendering(self):
        Permit = self.env['hse.permit']
        Loto = self.env['hse.loto.plan']

        permit = Permit.create({
            'title': 'Cold Work Line Inspection',
            'permit_type': 'cold_work',
            'location_id': self.test_loc.id,
            'requester_id': self.User.id,
        })

        loto = Loto.create({
            'title': 'Pump P-101 Isolation Scheme',
            'location_id': self.test_loc.id,
            'system_description': 'Suction & discharge valves locked shut',
            'energy_electrical': True,
        })

        # Test report action existence
        permit_report = self.env.ref('hse_reports.action_report_hse_permit', raise_if_not_found=False)
        self.assertIsNotNone(permit_report)
        self.assertEqual(permit_report.model, 'hse.permit')

        loto_report = self.env.ref('hse_reports.action_report_hse_loto', raise_if_not_found=False)
        self.assertIsNotNone(loto_report)
        self.assertEqual(loto_report.model, 'hse.loto.plan')

        # Test QWeb rendering without exceptions
        permit_html = permit_report._render_qweb_html(permit_report.report_name, [permit.id])
        self.assertTrue(len(permit_html[0]) > 0)

        loto_html = loto_report._render_qweb_html(loto_report.report_name, [loto.id])
        self.assertTrue(len(loto_html[0]) > 0)

    # =========================================================================
    # 36. Process Hazard Analysis (PHA) / HAZOP Study Suite
    # =========================================================================
    def test_36_hazop_study_and_deviation(self):
        Hazop = self.env['hse.hazop.study']
        Node = self.env['hse.hazop.node']
        Deviation = self.env['hse.hazop.deviation']
        Rec = self.env['hse.hazop.recommendation']

        study = Hazop.create({
            'title': 'Test Crude Distillation HAZOP',
            'location_id': self.test_loc.id,
            'study_type': 'hazop',
            'leader_id': self.User.id,
            'team_members': 'Lead Process Engineer, Lead Operator, Safety Specialist',
            'scope_description': 'Crude preheat train and furnace F-101',
            'pid_references': 'PID-100-01 Rev 5',
        })
        self.assertEqual(study.state, 'draft')
        study.action_start_session()
        self.assertEqual(study.state, 'in_session')

        node = Node.create({
            'study_id': study.id,
            'node_number': 1,
            'name': 'Node 1: Crude Charge Furnace F-101 Pass Tubes',
            'node_boundary': 'From pump discharge to furnace outlet manifold',
            'design_intent': 'Heat crude to 350°C at 15 barg without tube coking',
            'operating_press_range': '12 - 15 barg',
            'operating_temp_range': '280 - 350 °C',
        })
        self.assertEqual(node.node_number, 1)

        dev = Deviation.create({
            'node_id': node.id,
            'parameter': 'flow',
            'guide_word': 'no',
            'causes': 'Crude charge pump trip or control valve failure closed',
            'consequences': 'Tube overheating, metallurgical rupture, furnace fire',
            'unmitigated_severity': 5,
            'unmitigated_likelihood': 3,
            'existing_safeguards': 'Low pass flow switch alarm, automatic fuel gas shutdown interlock',
            'mitigated_severity': 4,
            'mitigated_likelihood': 1,
            'requires_lopa': True,
            'sil_target': 'sil2',
        })
        self.assertEqual(dev.deviation_text, 'No / None (Zero Flow/Feed) - Flow')
        self.assertEqual(dev.unmitigated_risk_score, 15)
        self.assertEqual(dev.mitigated_risk_score, 4)
        self.assertEqual(dev.risk_level, 'medium')

        rec = Rec.create({
            'deviation_id': dev.id,
            'recommendation': 'Install redundant flow transmitter on pass 2 with 1oo2 voting',
            'action_category': 'hardware',
            'assigned_department': 'instrumentation',
            'responsible_user_id': self.User.id,
            'target_date': fields.Date.today() + timedelta(days=60),
        })
        self.assertEqual(rec.state, 'draft')
        rec.action_assign()
        self.assertEqual(rec.state, 'assigned')
        rec.action_start()
        self.assertEqual(rec.state, 'in_progress')
        rec.action_complete()
        self.assertEqual(rec.state, 'completed')
        rec.action_verify_close()
        self.assertEqual(rec.state, 'verified')

        study._compute_counts()
        self.assertEqual(study.node_count, 1)
        self.assertEqual(study.recommendation_count, 1)
        self.assertEqual(study.open_recommendations_count, 0)

        study.action_submit_review()
        self.assertEqual(study.state, 'review')
        study.action_approve()
        self.assertEqual(study.state, 'approved')

    # =========================================================================
    # 37. Layers of Protection Analysis (LOPA) & SIL Determination
    # =========================================================================
    def test_37_lopa_study_math_and_sil(self):
        Lopa = self.env['hse.lopa.study']
        Ipl = self.env['hse.lopa.ipl']

        lopa = Lopa.create({
            'title': 'High Pressure Separator V-102 Gas Blowby to Low Pressure Vessel',
            'location_id': self.test_loc.id,
            'severity_category': 'cat3',
            'target_mitigated_frequency': 0.0001,
            'initiating_event_desc': 'Level control valve LCV-102 fails wide open',
            'initiating_event_freq': 0.1,
            'participants': 'Process Safety Specialist, Lead Instrument Engineer',
            'consequence_description': 'Overpressure and rupture of downstream atmospheric storage tank',
        })
        self.assertAlmostEqual(lopa.unmitigated_frequency, 0.1)

        # Add IPL 1: Independent High Pressure Alarm & Operator Response (PFD = 0.1)
        ipl1 = Ipl.create({
            'lopa_id': lopa.id,
            'name': 'PAH-102 Alarm & Manual Operator Intervention (15 min window)',
            'ipl_type': 'alarm',
            'pfd': 0.1,
            'is_valid_ipl': True,
        })

        # Add IPL 2: Pressure Relief Valve PSV-102 (PFD = 0.01)
        ipl2 = Ipl.create({
            'lopa_id': lopa.id,
            'name': 'Full Flow Relief Valve PSV-102 to Flare Header',
            'ipl_type': 'psv',
            'pfd': 0.01,
            'is_valid_ipl': True,
        })

        lopa._compute_lopa_math()
        # Combined PFD = 0.1 * 0.01 = 0.001
        self.assertAlmostEqual(lopa.total_ipl_pfd, 0.001, places=5)
        # Mitigated frequency = 0.1 * 0.001 = 0.0001
        self.assertAlmostEqual(lopa.mitigated_frequency, 0.0001, places=6)
        # Meets 1e-4 target
        self.assertTrue(lopa.target_met)
        self.assertEqual(lopa.required_sil, 'none')

        # Test scenario requiring SIL 2
        lopa.initiating_event_freq = 1.0 # higher demand
        lopa._compute_lopa_math()
        self.assertFalse(lopa.target_met)
        self.assertGreater(lopa.risk_reduction_factor, 1.0)
        self.assertIn(lopa.required_sil, ['sil1', 'sil2'])

        lopa.action_validate()
        self.assertEqual(lopa.state, 'validated')
        lopa.action_approve()
        self.assertEqual(lopa.state, 'approved')

    # =========================================================================
    # 38. Safety Critical Elements (SECE) & FARSI Performance Standards
    # =========================================================================
    def test_38_sece_farsi_standards_and_assurance(self):
        Sece = self.env['hse.sece']
        Assurance = self.env['hse.sece.assurance']

        sece = Sece.create({
            'tag': 'SECE-ESD-201',
            'name': 'Depressuring Blowdown Valve BDV-201',
            'location_id': self.test_loc.id,
            'sece_group': 'emergency_shutdown',
            'major_accident_hazard': 'Major fire / vessel rupture escalation',
            'functionality_std': 'Open within 2.0s upon ESD trip signal',
            'availability_std': 99.8,
            'reliability_std': 'SIL 2',
            'survivability_std': '60-min jet fire rating at 350 kW/m2',
        })
        self.assertEqual(sece.barrier_health, 'healthy')
        self.assertEqual(sece.state, 'active')

        # Record Assurance Test - Pass
        task_pass = Assurance.create({
            'sece_id': sece.id,
            'test_date': fields.Date.today(),
            'test_type': 'proof_test',
            'test_procedure_ref': 'SOP-ESD-BDV-TEST-001',
            'measured_parameters': 'Full stroke stroke time: 1.45s (Spec <= 2.0s)',
            'inspector_id': self.User.id,
            'result': 'pass',
        })
        self.assertEqual(task_pass.result, 'pass')

        # Record Assurance Test - Fail
        task_fail = Assurance.create({
            'sece_id': sece.id,
            'test_date': fields.Date.today(),
            'test_type': 'proof_test',
            'test_procedure_ref': 'SOP-ESD-BDV-TEST-001',
            'measured_parameters': 'Stroke failed due to solenoid valve failure',
            'inspector_id': self.User.id,
            'result': 'fail',
            'defects_noted': 'Solenoid coil burned out; actuator did not vent.',
        })
        sece.action_set_impaired()
        self.assertEqual(sece.barrier_health, 'failed')
        self.assertEqual(sece.state, 'impaired')

    # =========================================================================
    # 39. API RP 754 Process Safety Events (PSE Tier 1 & 2)
    # =========================================================================
    def test_39_process_safety_event_tiering(self):
        Pse = self.env['hse.pse']

        event = Pse.create({
            'title': 'Benzene Column Feed Line Gasket Blowout',
            'location_id': self.test_loc.id,
            'tier': 'tier1',
            'chemical_name': 'Benzene',
            'phase_of_release': 'liquid',
            'mass_released_kg': 1200.0,
            'threshold_quantity_kg': 500.0,
            'has_fire_explosion': True,
            'direct_cost': 150000.0,
            'barrier_failure_summary': 'Thermal fatigue of spiral wound gasket and failure of local fire detector.',
        })
        self.assertEqual(event.tier, 'tier1')
        self.assertTrue(event.threshold_exceeded)
        self.assertEqual(event.state, 'reported')

        event.action_investigate()
        self.assertEqual(event.state, 'investigating')
        event.action_classify()
        self.assertEqual(event.state, 'classified')
        event.action_regulatory_report()
        self.assertEqual(event.state, 'regulatory_reported')
        event.action_close()
        self.assertEqual(event.state, 'closed')

    # =========================================================================
    # 40. Air Emissions & Greenhouse Gas (GHG Protocol Scope 1/2)
    # =========================================================================
    def test_40_air_emissions_and_ghg(self):
        Air = self.env['hse.env.air.emission']

        emission = Air.create({
            'location_id': self.test_loc.id,
            'emission_point': 'Heater F-101 Flue Gas Stack',
            'scope': 'scope1',
            'source_type': 'stationary_combustion',
            'fuel_type': 'Natural Gas',
            'fuel_consumed': 200000.0,
            'fuel_unit': 'scf',
            'nox_kg': 42.5,
            'sox_kg': 1.2,
        })
        self.assertGreater(emission.co2_tonnes, 0.0)
        self.assertGreater(emission.co2e_tonnes, 0.0)
        self.assertEqual(emission.state, 'draft')
        emission.action_verify()
        self.assertEqual(emission.state, 'verified')
        emission.action_report()
        self.assertEqual(emission.state, 'reported')

    # =========================================================================
    # 41. Industrial Wastewater & Outfall Quality Monitoring
    # =========================================================================
    def test_41_wastewater_monitoring_compliance(self):
        Water = self.env['hse.env.water.monitoring']

        # Compliant Sample
        sample_ok = Water.create({
            'location_id': self.test_loc.id,
            'outfall_number': 'Outfall-001',
            'ph_level': 7.2,
            'bod_mg_l': 15.0,
            'cod_mg_l': 50.0,
            'tss_mg_l': 20.0,
            'oil_grease_mg_l': 2.0,
        })
        self.assertTrue(sample_ok.is_compliant)
        self.assertEqual(sample_ok.state, 'compliant')

        # Exceedance Sample
        sample_bad = Water.create({
            'location_id': self.test_loc.id,
            'outfall_number': 'Outfall-002 ETP Effluent',
            'ph_level': 10.5, # Exceeds 9.0
            'bod_mg_l': 55.0, # Exceeds 30
            'cod_mg_l': 200.0,# Exceeds 125
            'tss_mg_l': 85.0, # Exceeds 50
            'oil_grease_mg_l': 25.0, # Exceeds 10
        })
        self.assertFalse(sample_bad.is_compliant)
        self.assertEqual(sample_bad.state, 'exceedance')
        self.assertIn('pH', sample_bad.exceedance_parameters)
        self.assertIn('BOD', sample_bad.exceedance_parameters)

    # =========================================================================
    # 42. Hazardous Waste Manifest Tracking (EPA RCRA)
    # =========================================================================
    def test_42_hazardous_waste_rcra_manifest(self):
        Manifest = self.env['hse.env.waste.manifest']

        manifest = Manifest.create({
            'name': 'MAN-2026-9901',
            'location_id': self.test_loc.id,
            'generator_epa_id': 'TXD123456789',
            'waste_type': 'hazardous',
            'waste_description': 'RQ, Waste Flammable Liquid (Spent Toluene/Xylene)',
            'epa_waste_codes': 'D001, F003',
            'container_type': 'dm',
            'container_count': 8,
            'total_quantity': 1600.0,
            'unit_of_measure': 'kg',
            'transporter_company': 'EcoSafe Environmental Haulers',
            'transporter_epa_id': 'TXD987654321',
            'tsdf_facility_name': 'Clean Harbors Port Arthur TSDF',
            'tsdf_epa_id': 'TXD112233445',
            'accumulation_start_date': fields.Date.today(),
        })
        self.assertEqual(manifest.state, 'storage')
        self.assertGreater(manifest.storage_days_remaining, 0)
        self.assertLessEqual(manifest.storage_days_remaining, 90)

        manifest.action_ship()
        self.assertEqual(manifest.state, 'in_transit')
        manifest.action_tsdf_accept()
        self.assertEqual(manifest.state, 'accepted')
        manifest.action_certify_destruction()
        self.assertEqual(manifest.state, 'destroyed')
        self.assertTrue(manifest.certificate_of_disposal_received)

    # =========================================================================
    # 43. Chemical Spill & CERCLA Reportable Quantity Evaluation
    # =========================================================================
    def test_43_spill_cercla_reportable(self):
        Spill = self.env['hse.env.spill']

        # Spill exceeding Reportable Quantity
        spill = Spill.create({
            'title': 'Hexane Loading Arm Gasket Release',
            'location_id': self.test_loc.id,
            'substance_name': 'Hexane',
            'media_impacted': 'soil',
            'spill_source': 'pipe_rupture',
            'volume_released': 500.0,
            'volume_recovered': 450.0,
            'unit_of_measure': 'liters',
            'cercla_rq': 100.0,
            'containment_measures': 'Spill response trailer mobilized; vacuum truck recovered bulk liquid',
        })
        self.assertTrue(spill.is_reportable)
        self.assertEqual(spill.recovery_percentage, 90.0)
        self.assertEqual(spill.state, 'active')

        spill.action_contain()
        self.assertEqual(spill.state, 'contained')
        spill.action_start_recovery()
        self.assertEqual(spill.state, 'recovering')
        spill.action_remediate()
        self.assertEqual(spill.state, 'remediated')
        spill.action_close()
        self.assertEqual(spill.state, 'closed')

    # =========================================================================
    # 44. Industrial Hygiene Exposure Monitoring & 8-Hr TWA
    # =========================================================================
    def test_44_ih_exposure_monitoring_twa(self):
        Seg = self.env['hse.ih.seg']
        Sample = self.env['hse.ih.sample']

        seg = Seg.create({
            'name': 'Refinery Process Sample Draw Technicians',
            'code': 'SEG-LAB-01',
            'location_id': self.test_loc.id,
            'job_description': 'Manual sample drawing from pressurized sample bombs',
            'stressor_chemical': True,
        })
        self.assertEqual(seg.code, 'SEG-LAB-01')

        # Test Sample Within Action Level (< 50% PEL)
        sample_ok = Sample.create({
            'seg_id': seg.id,
            'sampling_type': 'air_chemical',
            'agent_name': 'Benzene',
            'measured_concentration': 0.2, # 0.2 ppm for 480 mins -> TWA 0.2 ppm
            'unit_of_measure': 'ppm',
            'sampling_duration_minutes': 480.0,
            'osha_pel': 1.0, # OSHA Benzene PEL = 1 ppm
            'acgih_tlv': 0.5,
        })
        self.assertAlmostEqual(sample_ok.twa_8hr, 0.2)
        self.assertEqual(sample_ok.exposure_rating, 'acceptable')

        # Test Overexposure (> PEL)
        sample_high = Sample.create({
            'seg_id': seg.id,
            'sampling_type': 'air_chemical',
            'agent_name': 'Benzene',
            'measured_concentration': 2.4, # 2.4 ppm for 480 mins -> TWA 2.4 ppm
            'unit_of_measure': 'ppm',
            'sampling_duration_minutes': 480.0,
            'osha_pel': 1.0,
            'acgih_tlv': 0.5,
        })
        self.assertTrue(sample_high.exceeds_pel)
        self.assertEqual(sample_high.exposure_rating, 'unacceptable')

    # =========================================================================
    # 45. Audiometry & Standard Threshold Shift (STS)
    # =========================================================================
    def test_45_audiometry_hearing_sts(self):
        Audio = self.env['hse.ih.audiometry']
        Emp = self.env['hr.employee'].search([], limit=1)
        if not Emp:
            Emp = self.env['hr.employee'].create({'name': 'John Safety Operator'})

        # Baseline Audiogram
        baseline = Audio.create({
            'employee_id': Emp.id,
            'test_date': fields.Date.today() - timedelta(days=365),
            'test_type': 'baseline',
            'audiologist_name': 'Dr. Sarah Connor, CCC-A',
            'l_2000': 10.0, 'l_3000': 15.0, 'l_4000': 15.0, # Avg = 13.3
            'r_2000': 10.0, 'r_3000': 15.0, 'r_4000': 15.0,
        })
        self.assertAlmostEqual(baseline.left_avg_234, 13.3, places=1)

        # Annual Audiogram with Standard Threshold Shift (STS)
        annual = Audio.create({
            'employee_id': Emp.id,
            'test_date': fields.Date.today(),
            'test_type': 'annual',
            'audiologist_name': 'Dr. Sarah Connor, CCC-A',
            'baseline_audiogram_id': baseline.id,
            'l_2000': 25.0, 'l_3000': 30.0, 'l_4000': 35.0, # Avg = 30.0 (Shift = 16.7 dB)
            'r_2000': 25.0, 'r_3000': 30.0, 'r_4000': 35.0,
        })
        self.assertTrue(annual.has_sts)
        self.assertTrue(annual.is_osha_recordable_sts)

    # =========================================================================
    # 46. Respirator Medical Clearance & PortaCount Fit Test
    # =========================================================================
    def test_46_respirator_fit_testing(self):
        Resp = self.env['hse.ih.respirator']
        Emp = self.env['hr.employee'].search([], limit=1)

        fit = Resp.create({
            'employee_id': Emp.id,
            'fit_test_date': fields.Date.today(),
            'next_due_date': fields.Date.today() + timedelta(days=365),
            'medical_clearance_status': 'cleared',
            'respirator_type': 'full_face',
            'manufacturer_model': '3M 6800 Series Full-Face',
            'mask_size': 'medium',
            'test_method': 'quantitative_portacount',
            'quantitative_fit_factor': 1500.0, # Spec >= 500
            'fit_test_passed': True,
            'clean_shaven_verified': True,
        })
        self.assertTrue(fit.fit_test_passed)
        self.assertEqual(fit.mask_size, 'medium')

    # =========================================================================
    # 47. Ergonomics Assessment (NIOSH & REBA)
    # =========================================================================
    def test_47_ergonomics_niosh_reba(self):
        Ergo = self.env['hse.ih.ergonomics']

        ergo_niosh = Ergo.create({
            'job_task_name': 'Drum Unloading from Truck Bed',
            'location_id': self.test_loc.id,
            'assessment_tool': 'niosh',
            'load_weight_kg': 20.0,
            'horizontal_distance_cm': 35.0,
            'vertical_height_cm': 75.0,
        })
        self.assertGreater(ergo_niosh.recommended_weight_limit, 0.0)
        self.assertGreater(ergo_niosh.lifting_index, 0.0)

        ergo_reba = Ergo.create({
            'job_task_name': 'Overhead Pipe Flange Bolting',
            'location_id': self.test_loc.id,
            'assessment_tool': 'reba',
            'reba_score': 9, # High risk (8-10)
        })
        self.assertEqual(ergo_reba.risk_level, 'high')

    # =========================================================================
    # 48. Contractor Prequalification & Worker Site Induction
    # =========================================================================
    def test_48_contractor_prequalification_and_induction(self):
        Contractor = self.env['hse.contractor']
        Induction = self.env['hse.contractor.induction']

        contr = Contractor.create({
            'name': 'Gulf Coast Specialized Scaffolding Inc',
            'trade_category': 'scaffolding',
            'emr_rate': 0.82,
            'trir_3year_avg': 0.70,
            'fatalities_last_5years': 0,
            'insurance_policy_number': 'POL-CGL-2026-881',
            'insurance_expiry_date': fields.Date.today() + timedelta(days=365),
            'safety_manual_approved': True,
        })
        self.assertEqual(contr.safety_grade, 'grade_a')

        ind = Induction.create({
            'contractor_id': contr.id,
            'worker_name': 'Carlos Ramirez',
            'national_id_passport': 'US-PASSPORT-448102',
            'job_title': 'Scaffolding Erector Level III',
            'expiry_date': fields.Date.today() + timedelta(days=365),
            'drug_alcohol_test_verified': True,
            'trade_certificates_verified': True,
        })
        self.assertEqual(ind.state, 'draft')
        ind.action_activate()
        self.assertEqual(ind.state, 'active')
        contr._compute_worker_count()
        self.assertEqual(contr.worker_count, 1)

    # =========================================================================
    # 49. Safety Data Sheets (SDS) & Chemical Compatibility
    # =========================================================================
    def test_49_sds_ghs_and_chemical_compatibility(self):
        Sds = self.env['hse.sds']
        Compat = self.env['hse.sds.compatibility']

        sds = Sds.create({
            'product_name': 'Anhydrous Ammonia (NH3)',
            'cas_number': '7664-41-7',
            'manufacturer_supplier': 'Industrial Chemical Supply Corp',
            'emergency_phone': '+1-800-424-9300',
            'signal_word': 'danger',
            'reactivity_group': 'toxic_gas',
            'ghs_skull_crossbones': True,
            'ghs_corrosion': True,
            'hazard_statements': 'H280: Contains gas under pressure. H314: Causes severe skin burns.',
            'precautionary_statements': 'P260: Do not breathe gas/vapors.',
            'storage_conditions': 'Store in cool, well-ventilated dedicated gas cylinder room.',
            'incompatible_materials': 'Acids, halogens, oxidizers.',
            'next_review_date': fields.Date.today() + timedelta(days=1000),
        })
        self.assertEqual(sds.signal_word, 'danger')

        rule = Compat.create({
            'group_a': 'strong_acid',
            'group_b': 'strong_base',
            'compatibility_status': 'forbidden',
            'reaction_hazard': 'Violent exothermic neutralization with violent boiling and spattering.',
        })
        self.assertEqual(rule.compatibility_status, 'forbidden')

    # =========================================================================
    # 50. Specialized High-Risk Permits: Critical Lift, Excavation, Radiography
    # =========================================================================
    def test_50_specialized_permits_lift_excavation_radio(self):
        Lift = self.env['hse.permit.critical.lift']
        Exc = self.env['hse.permit.excavation']
        Rad = self.env['hse.permit.radiography']

        # Critical Lift
        lift = Lift.create({
            'title': 'Heavy Reactor Top Head Lift',
            'location_id': self.test_loc.id,
            'crane_model': 'Demag CC 2800-1 (600 Tonne Crawler)',
            'crane_capacity_tonnes': 600.0,
            'boom_length_meters': 60.0,
            'operating_radius_meters': 24.0,
            'net_load_weight_tonnes': 85.0,
            'rigging_tackle_weight_tonnes': 5.0,
            'rated_capacity_at_radius': 110.0, # 90 / 110 = 81.8% -> Critical
            'rigging_engineer_id': self.User.id,
            'crane_operator_id': self.User.id,
        })
        self.assertTrue(lift.is_critical_lift)
        self.assertAlmostEqual(lift.lift_capacity_percentage, 81.8, places=1)
        lift.action_approve()
        self.assertEqual(lift.state, 'approved')

        # Excavation
        exc = Exc.create({
            'title': 'Excavation for Cooling Water Line Repair',
            'location_id': self.test_loc.id,
            'expected_completion': fields.Date.today() + timedelta(days=7),
            'excavation_depth_m': 2.2, # > 1.2m requires shoring
            'soil_type': 'type_b',
            'protective_system': 'hydraulic_shoring',
            'call_811_ticket_number': '811-TX-2026-90021',
            'competent_person_id': self.User.id,
        })
        exc.action_inspect()
        self.assertEqual(exc.state, 'inspected')
        exc.action_authorize()
        self.assertEqual(exc.state, 'authorized')

        # Radiography
        rad = Rad.create({
            'title': 'Gamma Radiography on Pipe Spool Welds',
            'location_id': self.test_loc.id,
            'source_type': 'ir192',
            'source_serial_no': 'IR-SPEC-2026-091',
            'activity_curies': 50.0,
            'radiation_protection_officer_id': self.User.id,
            'radiographer_name': 'David Kim, Level II RSO',
        })
        self.assertGreater(rad.controlled_boundary_radius_m, 20.0)
        rad.action_approve()
        self.assertEqual(rad.state, 'approved')

    # =========================================================================
    # 51. Emergency Response Plans (ERP) & Simulation Drills
    # =========================================================================
    def test_51_emergency_drill_muster_accountability(self):
        Erp = self.env['hse.emergency.plan']
        Drill = self.env['hse.emergency.drill']

        plan = Erp.create({
            'title': 'Refinery North Tank Farm Major Fire Response Plan',
            'location_id': self.test_loc.id,
            'emergency_type': 'hydrocarbon_fire',
            'incident_commander_id': self.User.id,
            'deputy_commander_id': self.User.id,
            'response_actions': 'Sound siren, start fire pumps, foam system activation',
            'internal_callout_list': 'Emergency Radio Channel 1',
            'external_agencies': 'Municipal Fire Dept (911)',
            'muster_stations': 'Assembly Area Alpha at Gate 1',
        })
        self.assertEqual(plan.state, 'active')

        drill = Drill.create({
            'plan_id': plan.id,
            'title': 'Quarterly Tank Farm Unannounced Fire Simulation Drill',
            'lead_evaluator_id': self.User.id,
            'total_personnel_on_site': 95,
            'total_personnel_mustered': 95,
            'ert_response_time_minutes': 2.8,
            'headcount_completion_minutes': 3.9,
            'drill_score_percent': 98.0,
            'strengths_observed': 'Immediate muster accountability within 4 minutes',
            'areas_for_improvement': 'Foam hose nozzle gasket required replacement',
        })
        self.assertEqual(drill.unaccounted_personnel, 0)
        self.assertEqual(drill.state, 'executed')
        drill.action_critique()
        self.assertEqual(drill.state, 'critiqued')
        drill.action_close()
        self.assertEqual(drill.state, 'closed')

    # =========================================================================
    # 52. Management System Audits & Behavior-Based Safety (BBS)
    # =========================================================================
    def test_52_audit_and_bbs_observation(self):
        Audit = self.env['hse.audit']
        Checklist = self.env['hse.audit.checklist']
        Bbs = self.env['hse.bbs.observation']

        audit = Audit.create({
            'title': 'OSHA 1910.119 Process Safety Management (PSM) Triennial Audit',
            'location_id': self.test_loc.id,
            'protocol': 'osha_psm',
            'target_end_date': fields.Date.today() + timedelta(days=14),
            'lead_auditor_id': self.User.id,
            'audit_team': 'Lead Auditor, Mechanical Integrity Specialist, Operations Rep',
        })

        # Add Checklist Line 1 - Compliant
        c1 = Checklist.create({
            'audit_id': audit.id,
            'requirement_clause': '1910.119(e) Process Hazard Analysis',
            'verification_criteria': 'Verify 5-year revalidation completed for all high-hazard units',
            'finding_type': 'compliant',
            'evidence_notes': 'HAZOP revalidation completed 2026-03 for CDU-100',
        })

        # Add Checklist Line 2 - Minor NC
        c2 = Checklist.create({
            'audit_id': audit.id,
            'requirement_clause': '1910.119(f) Operating Procedures',
            'verification_criteria': 'Verify annual certification of SOP accuracy',
            'finding_type': 'minor_nc',
            'evidence_notes': 'Two SOPs past annual review date by 30 days',
        })

        audit._compute_findings()
        self.assertEqual(audit.total_checks, 2)
        self.assertEqual(audit.compliant_count, 1)
        self.assertEqual(audit.minor_nc_count, 1)
        self.assertEqual(audit.compliance_score_percent, 50.0)

        # BBS Observation
        bbs = Bbs.create({
            'location_id': self.test_loc.id,
            'observer_id': self.User.id,
            'work_activity': 'Flange torquing with hydraulic torque wrench',
            'people_observed_count': 2,
            'safe_behaviors_count': 9,
            'at_risk_behaviors_count': 1,
            'cat_body_position': True,
            'cat_ppe': True,
            'immediate_coaching_feedback': 'Discussed pinch point risk between reaction arm and pipe flange.',
        })
        self.assertEqual(bbs.safe_behavior_index, 90.0)
        self.assertEqual(bbs.state, 'coached')

    # =========================================================================
    # 53. HAZOP QWeb PDF Report Generation & Rendering Check
    # =========================================================================
    def test_53_hazop_qweb_report_rendering(self):
        Hazop = self.env['hse.hazop.study']
        Node = self.env['hse.hazop.node']
        Deviation = self.env['hse.hazop.deviation']

        study = Hazop.create({
            'title': 'Piping Header HAZOP Review',
            'location_id': self.test_loc.id,
            'study_type': 'hazop',
            'leader_id': self.User.id,
            'team_members': 'Process Engineer, Operator, Safety Officer',
            'scope_description': 'Line 10-FL-04 from pump discharge to flare',
            'pid_references': 'PID-04-01 Rev 2',
        })
        node = Node.create({
            'study_id': study.id,
            'node_number': 1,
            'name': 'Node 1: Discharge Line',
            'node_boundary': 'P-101 discharge to column inlet',
            'design_intent': 'Deliver 150 m3/h crude at 15 barg',
        })
        dev = Deviation.create({
            'node_id': node.id,
            'parameter': 'pressure',
            'guide_word': 'more',
            'causes': 'Block valve closed against running pump',
            'consequences': 'Line overpressure',
            'existing_safeguards': 'Casing relief valve PSV-101',
        })

        hazop_report = self.env.ref('hse_reports.action_report_hse_hazop', raise_if_not_found=False)
        self.assertIsNotNone(hazop_report)
        self.assertEqual(hazop_report.model, 'hse.hazop.study')

        html = hazop_report._render_qweb_html(hazop_report.report_name, [study.id])
        self.assertTrue(len(html[0]) > 0)

    # =========================================================================
    # 54. Safety Instrumented Functions (SIF) PFDavg & SIL Verification
    # =========================================================================
    def test_54_sif_pfd_and_sil_compliance(self):
        Sif = self.env['hse.sif']

        sif = Sif.create({
            'name': 'SIF-01-PT-101',
            'description': 'High Pressure Trip on Separator V-101',
            'location_id': self.test_loc.id,
            'hazard_scenario': 'Overpressure leading to vessel rupture and fire',
            'target_safe_state': 'Close ESDV-101A/B and open blowdown valve BDV-101',
            'subsystem_sensor_type': 'pressure',
            'sensor_voting': '1oo2',
            'logic_solver_voting': '1oo2d',
            'final_element_voting': '1oo2',
            'sensor_lambda_du': 1.2e-6,
            'final_element_lambda_du': 2.0e-6,
            'common_cause_beta': 0.05,
            'proof_test_interval_months': 12.0,
            'required_sil': 'sil2',
        })
        self.assertLess(sif.total_pfd_avg, 1e-2)
        self.assertIn(sif.calculated_sil, ['sil2', 'sil3', 'sil4'])
        self.assertTrue(sif.sil_compliant)
        self.assertGreater(sif.risk_reduction_factor, 100.0)

        sif.action_activate()
        self.assertEqual(sif.state, 'active')
        sif.action_proof_test()
        self.assertEqual(sif.state, 'testing')
        sif.action_complete_test()
        self.assertEqual(sif.state, 'active')
        sif.action_impair()
        self.assertEqual(sif.state, 'impaired')

    # =========================================================================
    # 55. SIF Operational Demand & Trip Logging
    # =========================================================================
    def test_55_sif_operational_demand_log(self):
        Sif = self.env['hse.sif']
        Demand = self.env['hse.sif.demand']

        sif = Sif.create({
            'name': 'SIF-02-LT-102',
            'description': 'High Level Trip on Flash Drum V-102',
            'location_id': self.test_loc.id,
            'hazard_scenario': 'Liquid carryover to compressor suction',
            'target_safe_state': 'Trip crude pump P-102 and close SDV-102',
            'required_sil': 'sil1',
        })

        demand = Demand.create({
            'sif_id': sif.id,
            'demand_type': 'real_process_trip',
            'trip_cause': 'Upstream control valve stuck open causing sudden level rise',
            'actuation_time_seconds': 1.6,
            'success': True,
            'notes': 'All final elements actuated within SRS budget.',
        })
        sif._compute_demand_count()
        self.assertEqual(sif.demand_count, 1)

    # =========================================================================
    # 56. Quantitative Dispersion Modeling & Consequence Threat Zones
    # =========================================================================
    def test_56_chemical_dispersion_and_consequence(self):
        Disp = self.env['hse.dispersion.scenario']

        scenario = Disp.create({
            'name': 'Propane Sphere Pipeline Rupture Dispersion',
            'location_id': self.test_loc.id,
            'chemical_name': 'Propane',
            'molecular_weight': 44.1,
            'release_phase': 'two_phase',
            'release_type': 'continuous_plume',
            'total_mass_kg': 10000.0,
            'release_rate_kg_s': 20.0,
            'wind_speed_m_s': 3.0,
            'stability_class': 'd',
            'erpg_3_ppm': 100.0,
            'erpg_2_ppm': 30.0,
            'erpg_1_ppm': 5.0,
            'lfl_percent': 2.1,
        })
        scenario._compute_dispersion_footprint()
        self.assertGreater(scenario.erpg_3_dist_m, 0.0)
        self.assertGreater(scenario.erpg_2_dist_m, scenario.erpg_3_dist_m)
        self.assertGreater(scenario.erpg_1_dist_m, scenario.erpg_2_dist_m)
        self.assertGreater(scenario.lfl_100_dist_m, 0.0)
        self.assertGreater(scenario.recommended_evacuation_radius_m, 100.0)

        scenario.action_model()
        self.assertEqual(scenario.state, 'modeled')
        scenario.action_verify()
        self.assertEqual(scenario.state, 'verified')
        scenario.action_activate_emergency()
        self.assertEqual(scenario.state, 'active_emergency')

    # =========================================================================
    # 57. HFACS & TapRooT Human Factors Incident Analysis
    # =========================================================================
    def test_57_hfacs_human_factors_investigation(self):
        Investigation = self.env['incident.investigation']
        Hfacs = self.env['hse.investigation.hfacs']

        invest = Investigation.create({
            'ref_name': 'INV-2026-COMP-001',
            'summary': 'Compressor Seal Oil Failure Investigation',
            'immediate_cause': 'Lubrication pump tripped',
            'underlying_cause': 'Filter differential pressure alarm ignored',
            'root_cause': 'Maintenance procedure omitted alarm verification step',
        })

        hfacs = Hfacs.create({
            'investigation_id': invest.id,
            'name': 'HFACS Root Cause Analysis - Seal Oil',
            'act_skill_based_error': True,
            'act_routine_violation': True,
            'pre_mental_state': True,
            'sup_inadequate': True,
            'org_operational_process': True,
        })
        hfacs._compute_factor_index()
        self.assertEqual(hfacs.active_factors_count, 5)
        self.assertGreater(hfacs.human_error_index, 20.0)

    # =========================================================================
    # 58. Confined Space Permitting, Entrant Log & Continuous Gas Monitoring
    # =========================================================================
    def test_58_confined_space_permitting_and_gas_monitoring(self):
        Cse = self.env['hse.permit.confined.space']
        Entrant = self.env['hse.permit.cs.entrant']
        GasLog = self.env['hse.permit.cs.gas_log']

        cse = Cse.create({
            'space_identifier': 'Crude Distillation Column C-101 Bottom Sump',
            'location_id': self.test_loc.id,
            'space_classification': 'class_b',
            'isolation_verified': True,
            'rescue_team_notified': True,
            'attendant_name': 'Marcus Vance (Hole Watch Certified)',
            'ventilation_cfm_rate': 3000.0,
        })
        self.assertEqual(cse.state, 'draft')
        cse.state = 'pre_entry_check'
        cse.action_authorize_entry()
        self.assertEqual(cse.state, 'active_entry')

        # Add 2 entrants
        e1 = Entrant.create({
            'cse_id': cse.id,
            'worker_name': 'Elena Rostova',
            'badge_number': 'EMP-7712',
            'status': 'inside',
        })
        e2 = Entrant.create({
            'cse_id': cse.id,
            'worker_name': 'David Chen',
            'badge_number': 'CONTR-9901',
            'status': 'inside',
        })
        cse._compute_entrants()
        self.assertEqual(cse.active_entrants_count, 2)

        # Log Gas Sample (Safe)
        g1 = GasLog.create({
            'cse_id': cse.id,
            'oxygen_pct': 20.8,
            'combustible_lel_pct': 0.0,
            'h2s_ppm': 0.0,
            'co_ppm': 2.0,
        })
        self.assertTrue(g1.is_safe)
        self.assertFalse(g1.alarm_triggered)

        # Log Unsafe Gas Sample
        g2 = GasLog.create({
            'cse_id': cse.id,
            'oxygen_pct': 18.2, # Below 19.5%
            'combustible_lel_pct': 8.0, # Above 5%
            'h2s_ppm': 12.0, # Above 5 ppm
            'co_ppm': 35.0, # Above 25 ppm
        })
        self.assertFalse(g2.is_safe)
        self.assertTrue(g2.alarm_triggered)

        cse.action_suspend_entry()
        self.assertEqual(cse.state, 'suspended')

        # Both entrants log exit
        e1.action_log_exit()
        e2.action_log_exit()
        cse._compute_entrants()
        self.assertEqual(cse.active_entrants_count, 0)

        cse.action_close_entry()
        self.assertEqual(cse.state, 'closed')

    # =========================================================================
    # 59. SIMOPS Spatial Radar Collision Engine
    # =========================================================================
    def test_59_simops_rules_matrix_and_radar_collision(self):
        Matrix = self.env['hse.simops.matrix']
        Radar = self.env['hse.simops.radar.plot']

        rule = Matrix.create({
            'activity_type_a': 'hot_work',
            'activity_type_b': 'line_break',
            'compatibility': 'prohibited',
            'min_separation_distance_m': 50.0,
            'mitigation_required': 'Strict temporal de-confliction required.',
        })
        self.assertEqual(rule.compatibility, 'prohibited')

        # Operation 1 at (100, 100) with 25m radius
        op1 = Radar.create({
            'name': 'Welding on Pipe Rack Support',
            'location_id': self.test_loc.id,
            'grid_zone': 'Zone 2A',
            'coord_x': 100.0,
            'coord_y': 100.0,
            'hazard_radius_m': 25.0,
            'source_type': 'hot_work',
            'active': True,
        })

        # Operation 2 at (120, 100) with 20m radius (distance = 20m < 45m sum radii)
        op2 = Radar.create({
            'name': 'Flammable Hydrocarbon Line Break',
            'location_id': self.test_loc.id,
            'grid_zone': 'Zone 2A',
            'coord_x': 120.0,
            'coord_y': 100.0,
            'hazard_radius_m': 20.0,
            'source_type': 'line_break',
            'active': True,
        })

        op1._compute_simops_collisions()
        op2._compute_simops_collisions()

        self.assertTrue(op1.has_conflict)
        self.assertEqual(op1.conflict_count, 1)
        self.assertTrue(op2.has_conflict)
        self.assertIn('prohibited', op1.conflict_summary.lower())

    # =========================================================================
    # 60. ESG Carbon Accounting & Corporate Resource Circularity
    # =========================================================================
    def test_60_esg_carbon_accounting_and_resource_balance(self):
        Esg = self.env['hse.esg.accounting']

        esg = Esg.create({
            'reporting_year': 2026,
            'reporting_period': 'annual',
            'location_id': self.test_loc.id,
            'scope1_fuel_gas_tonnes': 10000.0,
            'scope1_diesel_tonnes': 500.0,
            'scope1_flaring_tonnes': 0.0,
            'scope1_fugitive_tonnes': 0.0,
            'electricity_consumed_mwh': 30000.0,
            'renewable_energy_recs_mwh': 10000.0, # 20000 MWh market-based
            'grid_emission_factor_kg_kwh': 0.40,
            'scope3_cat1_purchased_goods': 5000.0,
            'scope3_cat3_fuel_energy': 0.0,
            'scope3_cat4_logistics': 2000.0,
            'scope3_cat5_waste': 0.0,
            'scope3_cat6_travel': 0.0,
            'scope3_cat7_commuting': 0.0,
            'carbon_credits_purchased_t': 1500.0,
            'carbon_capture_storage_t': 0.0,
            'water_fresh_withdrawn_m3': 500000.0,
            'water_recycled_m3': 200000.0,
            'hazardous_waste_t': 100.0,
            'non_hazardous_waste_t': 900.0,
            'waste_recycled_t': 750.0,
            'production_output_tonnes': 100000.0,
        })

        esg._compute_ghg_totals()
        # Scope 1 = 10500
        self.assertEqual(esg.total_scope1_co2e, 10500.0)
        # Scope 2 Market = 20000 * 0.40 = 8000
        self.assertEqual(esg.scope2_market_based_co2e, 8000.0)
        # Scope 3 = 7000
        self.assertEqual(esg.total_scope3_co2e, 7000.0)
        # Gross = 10500 + 8000 + 7000 = 25500
        self.assertEqual(esg.total_gross_ghg_co2e, 25500.0)
        # Net = 25500 - 1500 = 24000
        self.assertEqual(esg.total_net_ghg_co2e, 24000.0)
        # Water recycling = 200000 / 700000 = 28.6%
        self.assertAlmostEqual(esg.water_recycling_ratio_pct, 28.6, places=1)
        # Landfill diversion = 750 / 1000 = 75.0%
        self.assertEqual(esg.landfill_diversion_rate_pct, 75.0)

        esg.action_internal_review()
        self.assertEqual(esg.state, 'internal_review')
        esg.action_third_party_assure()
        self.assertEqual(esg.state, 'third_party_assured')
        esg.action_publish()
        self.assertEqual(esg.state, 'published')

    # =========================================================================
    # 61. Biological Monitoring & ACGIH BEI Threshold Exceedance
    # =========================================================================
    def test_61_biological_monitoring_bei_exceedance(self):
        Bio = self.env['hse.ih.biological.monitoring']
        Emp = self.env['hr.employee'].search([], limit=1)

        # Compliant Sample
        s1 = Bio.create({
            'employee_id': Emp.id,
            'chemical_agent': 'benzene_spma',
            'sample_date': fields.Date.today(),
            'measured_value': 12.0,
            'bei_limit': 25.0,
            'unit_of_measure': 'μg/g creatinine',
        })
        self.assertFalse(s1.exceeds_bei)
        self.assertEqual(s1.state, 'normal')

        # Exceedance Sample
        s2 = Bio.create({
            'employee_id': Emp.id,
            'chemical_agent': 'lead_blood',
            'sample_date': fields.Date.today(),
            'measured_value': 45.0,
            'bei_limit': 20.0,
            'unit_of_measure': 'μg/dL',
            'medical_removal_required': True,
        })
        self.assertTrue(s2.exceeds_bei)
        self.assertEqual(s2.state, 'medical_removal')

    # =========================================================================
    # 62. Radiation Dosimetry (TLD) Cumulative Dose & Regulatory Limits
    # =========================================================================
    def test_62_radiation_dosimetry_tld_cumulative(self):
        Dose = self.env['hse.ih.radiation.dosimetry']
        Emp = self.env['hr.employee'].search([], limit=1)

        # Quarter 1 Dose (1.5 mSv)
        q1 = Dose.create({
            'employee_id': Emp.id,
            'tld_badge_number': 'TLD-2026-X11',
            'year': 2026,
            'monitoring_period': 'q1',
            'deep_dose_hp10_msv': 1.5,
            'annual_limit_msv': 20.0,
            'action_level_msv': 5.0,
        })
        self.assertEqual(q1.state, 'normal')

        # Quarter 2 Dose (4.2 mSv -> Cumulative 5.7 mSv, exceeds action level 5.0)
        q2 = Dose.create({
            'employee_id': Emp.id,
            'tld_badge_number': 'TLD-2026-X11',
            'year': 2026,
            'monitoring_period': 'q2',
            'deep_dose_hp10_msv': 4.2,
            'annual_limit_msv': 20.0,
            'action_level_msv': 5.0,
        })
        q2._compute_cumulative_dose()
        self.assertEqual(q2.annual_cumulative_dose_msv, 5.7)
        self.assertTrue(q2.is_action_level_exceeded)
        self.assertFalse(q2.is_limit_exceeded)
        self.assertEqual(q2.state, 'action_level')

    # =========================================================================
    # 63. IOGP Life-Saving Rules & Stop Work Authority (SWA)
    # =========================================================================
    def test_63_lifesaving_rules_and_stop_work_authority(self):
        Rule = self.env['hse.lifesaving.rule']
        Swa = self.env['hse.stop.work']
        Emp = self.env['hr.employee'].search([], limit=1)

        rule = Rule.search([('rule_category', '=', 'hot_work')], limit=1)
        if not rule:
            rule = Rule.create({
                'name': 'Hot Work Safety Rule',
                'code': 'LSR-TEST-HW',
                'rule_category': 'hot_work',
                'rule_description': 'Control flammables and ignition sources',
                'mandatory_expectations': '100% continuous gas test and fire watch required',
            })
        self.assertTrue(rule.name)

        swa = Swa.create({
            'intervenor_id': Emp.id,
            'location_id': self.test_loc.id,
            'rule_id': rule.id,
            'hazard_description': 'Grinding spark shower directed towards open oily water drain without fire blanket',
            'perceived_risk_level': 'high',
            'supervisor_id': Emp.id,
            'resolution_details': 'Oily water drain covered with certified fire blanket and water seal verified',
        })
        self.assertEqual(swa.state, 'stopped')
        swa.action_start_mitigation()
        self.assertEqual(swa.state, 'mitigating')
        swa.action_authorize_resumption()
        self.assertEqual(swa.state, 'resumed')
        self.assertTrue(swa.resumption_authorized)
        swa.action_commend_and_close()
        self.assertEqual(swa.state, 'commended')

    # =========================================================================
    # 64. API RP 754 Process Safety Leading & Lagging Accounting
    # =========================================================================
    def test_64_api_rp_754_process_safety_metrics_engine(self):
        PseMetric = self.env['hse.pse.metric']

        metric = PseMetric.create({
            'year': 2026,
            'period': 'annual',
            'location_id': self.test_loc.id,
            'total_employee_hours': 800000.0,
            'total_contractor_hours': 200000.0, # Total = 1,000,000 hrs
            'tier1_events_count': 0,
            'tier2_events_count': 1,
            'psm_training_completion_pct': 100.0,
            'moc_action_closure_pct': 100.0,
            'pha_action_closure_pct': 100.0,
            'safety_critical_maintenance_compliance_pct': 100.0,
        })
        metric._compute_hours()
        metric._compute_rates()
        metric._compute_health_index()

        self.assertEqual(metric.total_site_exposure_hours, 1000000.0)
        self.assertEqual(metric.pse_tier1_rate, 0.0)
        # 1 * 200,000 / 1,000,000 = 0.20
        self.assertEqual(metric.pse_tier2_rate, 0.2)
        self.assertEqual(metric.total_pse_rate, 0.2)
        # Leading avg = 100 - (1 * 10) = 90.0
        self.assertEqual(metric.process_safety_index, 90.0)

        metric.action_validate()
        self.assertEqual(metric.state, 'validated')
        metric.action_publish()
        self.assertEqual(metric.state, 'published')

    # =========================================================================
    # 65. Safety Culture Maturity Model (DuPont Bradley Curve)
    # =========================================================================
    def test_65_safety_culture_bradley_curve_maturity(self):
        Culture = self.env['hse.safety.culture.assessment']
        Emp = self.env['hr.employee'].search([], limit=1)

        assess = Culture.create({
            'name': '2026 Annual Refinery Safety Culture Evaluation',
            'location_id': self.test_loc.id,
            'lead_assessor_id': Emp.id,
            'score_leadership_commitment': 4.5,
            'score_workforce_engagement': 4.2,
            'score_hazard_reporting_just_culture': 4.0,
            'score_risk_awareness_discipline': 4.4,
            'score_continuous_learning': 4.4, # Avg = 4.3 -> Interdependent
        })
        assess.action_evaluate()
        self.assertEqual(assess.overall_maturity_score, 4.3)
        self.assertEqual(assess.bradley_curve_stage, 'interdependent')
        self.assertEqual(assess.state, 'evaluated')
        assess.action_approve_roadmap()
        self.assertEqual(assess.state, 'action_plan')
        assess.action_complete()
        self.assertEqual(assess.state, 'completed')

    # =========================================================================
    # 66. LDAR Fugitive Emissions (EPA Method 21) & Repair Clocks
    # =========================================================================
    def test_66_ldar_fugitive_components_and_leak_detection(self):
        Comp = self.env['hse.ldar.component']
        Reading = self.env['hse.ldar.reading']

        comp = Comp.create({
            'tag_number': 'VALVE-HCU-102',
            'location_id': self.test_loc.id,
            'component_type': 'valve',
            'service_stream': 'gas_vapor',
            'leak_threshold_ppm': 500.0,
        })
        self.assertEqual(comp.tag_number, 'VALVE-HCU-102')

        # Reading 1: Compliant (25 ppm)
        r1 = Reading.create({
            'component_id': comp.id,
            'screening_value_ppm': 25.0,
            'background_ppm': 5.0,
        })
        self.assertFalse(r1.is_leak)
        self.assertEqual(r1.state, 'compliant')

        # Reading 2: Leak Detected (1800 ppm > 500 ppm)
        r2 = Reading.create({
            'component_id': comp.id,
            'screening_value_ppm': 1805.0,
            'background_ppm': 5.0,
        })
        self.assertTrue(r2.is_leak)
        self.assertEqual(r2.state, 'leaking')
        self.assertTrue(comp.is_leaking)

        # Repaired & Re-monitored Pass
        r2.write({
            'first_attempt_date': fields.Date.today(),
            'final_repair_date': fields.Date.today(),
        })
        self.assertEqual(r2.state, 'repaired')

    # =========================================================================
    # 67. Safety Barrier Integrity Elements & Degradation States
    # =========================================================================
    def test_67_safety_barrier_integrity_and_degradation(self):
        Barrier = self.env['hse.barrier.element']

        barrier = Barrier.create({
            'name': 'BARRIER-ESD-101 Depressuring System',
            'location_id': self.test_loc.id,
            'barrier_type': 'hardware',
            'barrier_role': 'mitigation',
            'health_status': 'effective',
        })
        self.assertFalse(barrier.is_impaired)

        barrier.action_set_degraded()
        self.assertEqual(barrier.health_status, 'degraded')
        self.assertTrue(barrier.is_impaired)

        barrier.action_set_failed()
        self.assertEqual(barrier.health_status, 'failed')
        self.assertTrue(barrier.is_impaired)

        barrier.action_set_healthy()
        self.assertEqual(barrier.health_status, 'effective')
        self.assertFalse(barrier.is_impaired)

    # =========================================================================
    # 68. Statutory Compliance Calendar & Compliance Obligations
    # =========================================================================
    def test_68_compliance_obligations_calendar(self):
        Reg = self.env['hse.regulation']
        Task = self.env['hse.compliance.task']

        reg = Reg.create({
            'name': 'OSHA 1904 Recording and Reporting Occupational Injuries and Illnesses',
            'code': '29 CFR 1904',
            'regulatory_body': 'OSHA',
            'category': 'occupational_safety',
        })

        # Scheduled task in future
        task = Task.create({
            'name': 'OSHA Form 300A Annual Posting & Submission',
            'regulation_id': reg.id,
            'regulatory_body': 'OSHA',
            'task_type': 'statutory_filing',
            'frequency': 'annual',
            'due_date': fields.Date.today() + timedelta(days=45),
            'lead_time_days': 30,
            'responsible_id': self.env.user.id,
        })
        self.assertEqual(task.state, 'scheduled')
        self.assertFalse(task.is_overdue)
        self.assertEqual(task.alert_date, fields.Date.today() + timedelta(days=15))

        # Lifecycle
        task.action_start()
        self.assertEqual(task.state, 'in_progress')

        task.action_submit()
        self.assertEqual(task.state, 'submitted')
        self.assertEqual(task.submission_date, fields.Date.today())

        task.action_verify()
        self.assertEqual(task.state, 'completed')

        # Overdue task in past
        task_overdue = Task.create({
            'name': 'EPA SARA Title III Tier II Emergency Inventory',
            'regulation_id': reg.id,
            'regulatory_body': 'EPA',
            'task_type': 'statutory_filing',
            'frequency': 'annual',
            'due_date': fields.Date.today() - timedelta(days=10),
            'state': 'scheduled',
            'responsible_id': self.env.user.id,
        })
        self.assertTrue(task_overdue.is_overdue)

    # =========================================================================
    # 69. Training Matrix & Competency Gap Analysis Engine
    # =========================================================================
    def test_69_training_matrix_and_gap_analysis(self):
        Competency = self.env['hse.competency']
        RoleComp = self.env['hse.role.competency']
        EmpComp = self.env['hse.employee.competency']
        Job = self.env['hr.job']
        Employee = self.env['hr.employee']
        Matrix = self.env['hse.training.matrix']

        # Create Job & Employees
        operator_job = Job.create({'name': 'Senior Process Technician QA'})
        emp1 = Employee.create({'name': 'Alex Rivera Test', 'job_id': operator_job.id})
        emp2 = Employee.create({'name': 'Sara Connor Test', 'job_id': operator_job.id})

        # Competency definitions
        comp_agt = Competency.create({
            'name': 'Authorized Gas Tester (AGT Level 1)',
            'code': 'CMP-AGT-TM-01',
            'category': 'gas_testing',
            'description': 'Testing for flammable, toxic, and oxygen-depleted atmospheres.',
        })
        comp_loto = Competency.create({
            'name': 'Lockout / Tagout Hazardous Energy Isolation',
            'code': 'CMP-LOTO-TM-01',
            'category': 'control_of_work',
            'description': 'Energy isolation standards.',
        })

        # Role requirements
        RoleComp.create({
            'job_id': operator_job.id,
            'competency_id': comp_agt.id,
            'minimum_level': 'level3',
            'is_mandatory': True,
        })
        RoleComp.create({
            'job_id': operator_job.id,
            'competency_id': comp_loto.id,
            'minimum_level': 'level3',
            'is_mandatory': True,
        })

        # emp1 is compliant in AGT but expired in LOTO
        EmpComp.create({
            'employee_id': emp1.id,
            'competency_id': comp_agt.id,
            'proficiency_level': 'level3',
            'assessment_date': fields.Date.today() - timedelta(days=100),
            'expiry_date': fields.Date.today() + timedelta(days=265),
            'assessor_id': self.env.user.id,
        })
        EmpComp.create({
            'employee_id': emp1.id,
            'competency_id': comp_loto.id,
            'proficiency_level': 'level3',
            'assessment_date': fields.Date.today() - timedelta(days=400),
            'expiry_date': fields.Date.today() - timedelta(days=35),
            'assessor_id': self.env.user.id,
        })

        matrix = Matrix.create({
            'name': 'Plant Operations Safety Qualification Audit 2026',
            'job_ids': [(6, 0, [operator_job.id])],
            'evaluation_date': fields.Date.today(),
            'evaluated_by': self.env.user.id,
        })

        matrix.action_evaluate_matrix()
        self.assertEqual(matrix.state, 'calculated')
        self.assertEqual(matrix.total_evaluated, 4)
        self.assertEqual(matrix.compliant_count, 1)
        self.assertEqual(matrix.gap_count, 3)
        self.assertEqual(matrix.compliance_rate, 25.0)

        # Generate corrective action tasks
        matrix.action_generate_training_actions()
        self.assertEqual(matrix.state, 'actions_generated')

        created_actions = self.env['hse.action'].search([
            ('title', 'ilike', 'Training Gap%')
        ])
        self.assertGreaterEqual(len(created_actions), 3)

    # =========================================================================
    # 70. Safety Observation Evidence and Location Profile
    # =========================================================================
    def test_70_observation_evidence_and_location(self):
        Observation = self.env['observation.observation']
        fake_photo_bytes = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='

        obs = Observation.create({
            'observation': 'Hydraulic fluid leak observed near compressor discharge flange',
            'employee_observer_name': 'David Banner',
            'employee_code': 'TECH-902',
            'priority': '3',
            'hazard_type': 'physical',
            'location_id': self.test_loc.id,
            'hazard_photo': fake_photo_bytes,
            'hazard_photo_filename': 'leak_evidence.png',
        })
        self.assertEqual(obs.location_id.id, self.test_loc.id)
        self.assertTrue(bool(obs.hazard_photo))
        self.assertEqual(obs.hazard_photo_filename, 'leak_evidence.png')

    # =========================================================================
    # 71. Safety Committee & Toolbox Meetings Integration
    # =========================================================================
    def test_71_safety_meetings_and_toolbox_talks(self):
        if 'hse.meeting.department' in self.env:
            Dept = self.env['hse.meeting.department']
            MeetingType = self.env['hse.meeting.type']
            Meeting = self.env['hse.meeting']

            dept = Dept.create({
                'name': 'Offshore Drilling Operations Unit',
                'number_of_employees': 50,
            })
            m_type = MeetingType.create({
                'name': 'Pre-Shift Toolbox Safety Talk'
            })

            meeting = Meeting.create({
                'department_id': dept.id,
                'meeting_type_ids': m_type.id,
                'topic': 'Simultaneous Operations (SIMOPS) Awareness & Barrier Management',
                'present_employees': 40,
                'meeting_attend_employees': 38,
                'duration': 1.0,
            })
            self.assertEqual(meeting.total_employees, 50)
            self.assertAlmostEqual(meeting.percentage_total_attendees, 76.0, places=1)
        else:
            self.assertTrue(True)

    # =========================================================================
    # 72. Dashboard Controller Enhanced KPIs
    # =========================================================================
    def test_72_dashboard_controller_enhanced_kpis(self):
        import json as _json
        from odoo.http import Response as _HttpResponse
        controller = hse_dashboard_controller.HSEDashboardController()
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.make_json_response.side_effect = (
            lambda data, headers=None, cookies=None, status=200: _HttpResponse(
                response=_json.dumps(data), status=status, content_type='application/json')
        )
        with patch.object(hse_dashboard_controller, 'request', mock_req):
            response = controller.get_dashboard_data()
            data = _json.loads(response.get_data(as_text=True))
            self.assertIn('compliance_tasks_overdue', data)
            self.assertIn('compliance_tasks_active', data)
            self.assertIn('training_gap_count', data)
            self.assertIn('safety_meetings_count', data)
            self.assertIn('barrier_health_pct', data)
            self.assertIn('trir', data)






