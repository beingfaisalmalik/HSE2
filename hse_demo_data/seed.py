"""Connected, fictional client-demo scenarios. Never install in a production DB.

Every created record has a stable, noupdate external ID. Re-running the loader
adds missing samples without overwriting edits made during a presentation.
Dates are anchored to the first installation, not moved on every upgrade.
"""
from datetime import timedelta
import base64

from odoo import Command, fields, tools


class DemoSeeder:
    def __init__(self, env):
        self.env = env
        self.today = fields.Date.context_today(env['res.users'])
        self.now = fields.Datetime.now()
        self.owner = self.ref('base.user_admin')
        self.unit100 = self.ref('dd_loc_unit100')
        self.unit200 = self.ref('dd_loc_unit200')
        self.warehouse = self.ref('dd_loc_wh')

    def ref(self, xmlid):
        return self.env.ref(xmlid if '.' in xmlid else 'hse_demo_data.' + xmlid).id

    def date(self, days=0):
        return self.today + timedelta(days=days)

    def time(self, days=0, hours=0):
        return self.now + timedelta(days=days, hours=hours)

    def seed(self, xmlid, model, **values):
        complete = 'hse_demo_data.' + xmlid
        existing = self.env.ref(complete, raise_if_not_found=False)
        if existing and existing.exists():
            return existing
        record = self.env[model].with_context(
            tracking_disable=True, mail_create_nosubscribe=True,
            no_reset_password=True,
        ).create(values)
        self.env['ir.model.data'].create({
            'module': 'hse_demo_data', 'name': xmlid,
            'model': model, 'res_id': record.id, 'noupdate': True,
        })
        return record

    def run(self):
        self._people_and_reference()
        self._risk_and_investigation()
        self._process_safety()
        self._environment_and_health()
        self._control_of_work()
        self._emergency_and_contractors()
        self._governance_and_reliability()
        self._enrich_existing_scenarios()

    def _people_and_reference(self):
        s, r = self.seed, self.ref
        # No shared passwords in the addon. Provision passwords out-of-band.
        s('dd_user_presenter', 'res.users', name='Elena Morris · Demo Presenter',
          login='hse.presenter', email='elena.morris@northstar.example',
          action_id=r('hse_demo_data.action_client_demo'),
          groups_id=[Command.set([r('base.group_user'), r('hse.group_manager'),
                                 r('hse_demo_data.group_demo_presenter'),
                                 r('hr.group_hr_user')])])
        s('dd_user_contractor', 'res.users', name='Alex Morgan · Demo Contractor',
          login='hse.contractor', email='alex.morgan@contractor.example',
          groups_id=[Command.set([r('base.group_portal')])])
        s('dd_dept_hse', 'hr.department', name='Health, Safety & Environment')
        s('dd_emp_elena', 'hr.employee', name='Elena Morris',
          user_id=r('dd_user_presenter'), department_id=r('dd_dept_hse'),
          work_email='elena.morris@northstar.example')
        s('dd_plant', 'hse.location.profile', name='Northstar Petrochemicals · Demo Complex',
          code='NS-DEMO', location_type='plant', hazardous_zone='zone2',
          evacuation_route='Fictional facility: follow marked routes to Muster Alpha; use Bravo if downwind.',
          notes='<p>Synthetic client demonstration only. No operational or emergency use.</p>')
        for xmlid, name in [('dd_legacy_unit100', 'Cracker Unit-100'),
                            ('dd_legacy_unit200', 'Polyethylene Unit-200')]:
            s(xmlid, 'location.form', name=name)
        s('dd_analysis', 'analysis.form', name='V-101 inspection and safe return to service')
        s('dd_hazard_chemical', 'hazard.setting.model', name='Residual hydrocarbon atmosphere',
          description='Vapor remaining after draining and purging.', category='chemical', severity='high')
        s('dd_hazard_physical', 'hazard.setting.model', name='Unexpected energization',
          description='Stored energy or restart during maintenance.', category='physical', severity='high')
        s('dd_severity_major', 'severity.level', name='4 · Major',
          description='Serious injury or major asset damage; example classification only.')
        s('dd_inc_category', 'incident.category', name='Maintenance / energy isolation')
        s('dd_body_hand', 'ir.body.part', ir_body_part='Right hand / fingers',
          ir_body_des='Synthetic hand-injury classification.')
        s('dd_grade_lti', 'injury.create.level', name='Lost-time injury (illustrative)',
          code='LTI', description='Time-away example for the fictional scenario.')
        for xmlid, label, code in [
            ('dd_control_isolation', 'Positive isolation and zero-energy verification', 'ENG-LOTO'),
            ('dd_control_gas', 'Pre-entry gas test and continuous atmospheric monitoring', 'ADM-GAS'),
            ('dd_control_barricade', 'Physical exclusion zone with a dedicated attendant', 'ENG-BAR'),
        ]:
            s(xmlid, 'ra_jsa.control', control_measure=label, code=code,
              supporting_information='Verify at the worksite before authorizing the task.')
        s('dd_sds_benzene', 'hse.sds', product_name='Benzene · illustrative SDS',
          cas_number='71-43-2', chemical_formula='C6H6', un_number='UN 1114',
          manufacturer_supplier='Northstar Chemicals (fictional)',
          emergency_phone='DEMO ONLY — NOT AN EMERGENCY NUMBER',
          revision_date=self.date(-90), next_review_date=self.date(1000),
          hazard_statements='Illustrative only: flammable liquid; carcinogenic exposure hazard. Consult the real supplier SDS.',
          precautionary_statements='Use closed transfer, ignition control and approved PPE. Demo text is not an authoritative SDS.',
          storage_conditions='Segregated flammable storage with secondary containment.',
          incompatible_materials='Strong oxidizers; consult the actual supplier SDS.',
          ghs_health_hazard=True, ghs_skull_crossbones=False,
          flash_point_c=-11.0, boiling_point_c=80.1, state='current')
        s('dd_sds_caustic', 'hse.sds', product_name='Sodium hydroxide solution · illustrative SDS',
          cas_number='1310-73-2', chemical_formula='NaOH', un_number='UN 1824',
          manufacturer_supplier='Northstar Chemicals (fictional)',
          emergency_phone='DEMO ONLY — NOT AN EMERGENCY NUMBER',
          revision_date=self.date(-1080), next_review_date=self.date(15),
          hazard_statements='Illustrative corrosive-material example; not a substitute for a supplier SDS.',
          precautionary_statements='Prevent splashes; verify chemical gloves, face protection and eyewash access.',
          storage_conditions='Dedicated corrosive storage; separate from acids.',
          incompatible_materials='Strong acids and incompatible metals.',
          reactivity_group='strong_base', ghs_flame=False, ghs_corrosion=True,
          ghs_skull_crossbones=False, ghs_environment=False, state='review_due')
        s('dd_chemical_benzene', 'hse.location.chemical', location_id=self.unit100,
          chemical_name='Benzene', cas_number='71-43-2', physical_state='liquid',
          nfpa_health=2, nfpa_flammability=3, nfpa_instability=0,
          quantity_stored=2500, unit_of_measure='kg',
          sds_url='/web#id=%s&model=hse.sds&view_type=form' % r('dd_sds_benzene'),
          ghs_flammable=True, ghs_carcinogen=True)
        s('dd_chemical_caustic', 'hse.location.chemical', location_id=self.warehouse,
          chemical_name='Sodium hydroxide solution', cas_number='1310-73-2',
          nfpa_health=3, nfpa_flammability=0, quantity_stored=1200,
          ghs_corrosive=True)
        s('dd_compatibility', 'hse.sds.compatibility', group_a='strong_acid', group_b='strong_base',
          compatibility_status='forbidden',
          reaction_hazard='Illustrative segregation rule: exothermic reaction and corrosive splashing.')
        matrix = r('hse.matrix_standard_5x5')
        for severity in range(1, 6):
            for likelihood in range(1, 6):
                s('dd_matrix_%s_%s' % (severity, likelihood), 'hse.risk.matrix.cell',
                  matrix_id=matrix, consequence_level=severity, likelihood_level=likelihood,
                  action_required='Use the approved site risk acceptance process; demo configuration only.')

    def _risk_and_investigation(self):
        s, r = self.seed, self.ref
        hazards = [
            ('atmosphere', 'Residual hydrocarbon vapor during vessel entry', 5, 4, 5, 1, 'dd_control_gas'),
            ('restart', 'Unexpected restart of isolated equipment', 4, 3, 4, 1, 'dd_control_isolation'),
            ('dropped', 'Dropped tools at the vessel manway', 3, 2, 2, 1, 'dd_control_barricade'),
            ('handling', 'Manual handling of inspection equipment', 2, 1, 1, 1, 'dd_control_barricade'),
        ]
        for key, name, severity, likelihood, post_s, post_l, control in hazards:
            s('dd_hazard_' + key, 'ra_jsa.hazard', name=name, ra_id=r('dd_jsa_1'),
              hazards_selection=r('dd_hazard_chemical' if key == 'atmosphere' else 'dd_hazard_physical'),
              description=name, consequences='Personnel injury and loss of containment.',
              severity_level=str(severity), likelihood=str(likelihood),
              post_severity_level=str(post_s), post_likelihood=str(post_l),
              control_ids=[Command.set([r(control)])],
              control_description='Apply the linked control and verify at the point of work.')
        s('dd_legacy_capa', 'hse.capa.model', name='Re-verify isolation following interruption',
          ra_jsa_id=r('dd_jsa_1'), incident_reporting_id=r('dd_inc_lti1'),
          incident_investigation_id=r('dd_inv_lti1'), assigned_person=r('dd_emp_john'),
          description='Re-verify locks, stored-energy release and the restart hold point following any interruption.',
          responsible_user_id=r('dd_user_presenter'), select_department=r('dd_dept_maintenance'),
          ra_reference_number='Northstar V-101 JSA / K-301 learning review',
          comments='Linked to the injury investigation and shared through the maintenance toolbox.',
          due_date=self.date(7), status='in_progress', action_type='corrective', select_capa='corrective')
        s('dd_legacy_preventive', 'hse.preventive.model', name='Add interruption recovery to toolbox brief',
          ra_jsa_id=r('dd_jsa_1'), action_description='Review the approved restart sequence at each shift briefing.',
          due_date=self.date(10), responsible_user_id=r('dd_user_presenter'))
        inv = r('dd_inv_lti1')
        whys = [
            ('Why was the hand injured?', 'The coupling moved while the hand was within the pinch point.'),
            ('Why did equipment move?', 'A restart was initiated after an interruption without re-verification.'),
            ('Why was re-verification omitted?', 'The restart checklist did not define an interruption hold point.'),
            ('Why was the hold point absent?', 'Procedure review did not assess interruption and handover risks.'),
            ('Why did review miss these risks?', 'The review standard lacked human-factors and field-worker input.'),
        ]
        for i, (question, answer) in enumerate(whys, 1):
            s('dd_why_%s' % i, 'hse.investigation.why', investigation_id=inv,
              why_number=i, question=question, answer=answer, is_root_cause=i == 5)
        for category, cause in [
            ('man', 'Task interruption and ambiguous restart ownership'),
            ('machine', 'Accessible pinch point during guard repositioning'),
            ('method', 'Missing interruption/restart hold point'),
            ('material', 'Guard fasteners required repositioning'),
            ('measurement', 'Local zero-energy confirmation not repeated'),
            ('environment', 'Shift handover and production time pressure'),
        ]:
            s('dd_fishbone_' + category, 'hse.investigation.fishbone', investigation_id=inv,
              category=category, cause_description=cause,
              significance='root' if category == 'method' else 'contributing')
        for i, (label, event_type) in enumerate([
            ('Maintenance task interrupted for shift briefing', 'initiating'),
            ('Restart initiated without repeating hold-point checks', 'escalation'),
            ('Hand pinch injury reported; work stopped and equipment isolated', 'injury'),
            ('First aid and clinic assessment arranged; scene preserved', 'containment'),
        ], 1):
            s('dd_timeline_%s' % i, 'hse.investigation.timeline', investigation_id=inv,
              event_time=self.time(-24, i / 10), description=label,
              source_evidence='Synthetic witness statement and training historian extract')
            s('dd_inc_event_%s' % i, 'hse.incident.event', incident_id=r('dd_inc_lti1'),
              sequence=i * 10, event_time=self.time(-24, i / 10), title=label,
              event_type=event_type)
        for i, (side, name, status, category) in enumerate([
            ('preventive', 'Interruption/restart checklist', 'failed', 'procedural'),
            ('preventive', 'Zero-energy witness confirmation', 'degraded', 'human'),
            ('mitigative', 'Accessible stop button and work-stop response', 'effective', 'engineered_active'),
            ('mitigative', 'First-aid response and clinic transfer', 'effective', 'human'),
        ], 1):
            s('dd_bowtie_%s' % i, 'hse.bowtie.barrier', investigation_id=inv,
              side=side, barrier_name=name, barrier_status=status, barrier_category=category,
              threat_or_consequence='Unexpected movement / personnel injury',
              failure_mechanism='See 5 Whys and procedure review findings.' if status != 'effective' else False,
              action_id=r('dd_capa_1') if status != 'effective' else False)
        s('dd_hfacs', 'hse.investigation.hfacs', investigation_id=inv,
          name='Interruption and shift-handover human factors',
          act_skill_based_error=True, pre_crew_resource_mgt=True, sup_inadequate=True,
          org_operational_process=True, act_narrative='Restart step missed after interruption.',
          preconditions_narrative='No explicit transfer of restart authority at handover.',
          organization_narrative='Procedure review standard omitted interruption recovery.',
          corrective_actions_hf='Introduce a hold point, clarify restart authority, verify through field observation.')
        s('dd_culture', 'hse.safety.culture.assessment', name='Northstar workforce culture baseline',
          location_id=self.unit100, lead_assessor_id=r('dd_emp_elena'),
          assessment_date=self.date(-30), participants_count=86,
          score_leadership_commitment=4.2, score_workforce_engagement=3.4,
          score_hazard_reporting_just_culture=3.1, score_risk_awareness_discipline=3.8,
          score_continuous_learning=3.6, strengths='Workers exercise stop-work authority without reprisal.',
          vulnerabilities='Night-shift learning and interruption handover need improvement.',
          roadmap_actions='Weekly leadership walk, feedback on every report, and 90-day reassessment.', state='action_plan')

    def _process_safety(self):
        s, r = self.seed, self.ref
        s('dd_hazop', 'hse.hazop.study', title='R-201 / T-201 level protection revalidation',
          location_id=self.unit200, leader_id=r('dd_user_presenter'),
          team_members='Elena Morris (HSE), Ahmed Raza (Operations), John Dsouza (Maintenance), process and instrument engineers',
          scope_description='Review feed, high-level protection and safe shutdown before transmitter modification.',
          pid_references='DEMO-PID-PE200-014 Rev C', date=self.date(-18),
          target_completion_date=self.date(12), state='action_tracking')
        s('dd_hazop_node', 'hse.hazop.node', study_id=r('dd_hazop'),
          name='T-201 feed and level protection', node_number=1,
          node_boundary='Feed isolation valve to vessel outlet and associated instrument loops.',
          design_intent='Maintain vessel inventory within the approved operating envelope.',
          operating_press_range='Illustrative: 8–12 barg', flow_medium='Hydrocarbon process feed')
        s('dd_hazop_deviation', 'hse.hazop.deviation', node_id=r('dd_hazop_node'),
          parameter='level', guide_word='more', causes='Fouled DP transmitter reads low; feed valve remains open.',
          consequences='Vessel overfill and hydrocarbon loss of containment.',
          existing_safeguards='Independent high-high level trip, alarm response, and containment bund.',
          unmitigated_severity=5, unmitigated_likelihood=4,
          mitigated_severity=5, mitigated_likelihood=2, requires_lopa=True, sil_target='sil2')
        s('dd_hazop_action', 'hse.action', title='Verify independence of replacement high-high level protection',
          description='Document independence, failure data and proof-test requirements before final design approval.',
          source_type='moc', source_reference='T-201 HAZOP / transmitter MOC',
          moc_id=r('dd_moc_1'), assigned_to=r('dd_user_presenter'), priority='2',
          target_date=self.date(12), progress=35, state='in_progress')
        s('dd_hazop_recommendation', 'hse.hazop.recommendation', deviation_id=r('dd_hazop_deviation'),
          recommendation='Replace the fouling-prone transmitter and validate independent high-high level protection.',
          action_category='hardware', assigned_department='instrumentation',
          responsible_user_id=r('dd_user_presenter'), target_date=self.date(12),
          moc_id=r('dd_moc_1'), action_id=r('dd_hazop_action'), state='in_progress')
        s('dd_lopa', 'hse.lopa.study', title='T-201 overfill following level-control failure',
          location_id=self.unit200, hazop_deviation_id=r('dd_hazop_deviation'),
          participants='Process, operations, instrumentation and HSE technical reviewers',
          consequence_description='Illustrative overfill scenario with potential flammable release.',
          initiating_event_desc='Control transmitter fails low and feed valve remains open.',
          initiating_event_freq=0.1, target_mitigated_frequency=0.0001,
          recommendations='Validate the allocated SIL against site criteria; calculations are illustrative.', state='validated')
        s('dd_lopa_ipl', 'hse.lopa.ipl', lopa_id=r('dd_lopa'), name='Independent operator alarm response',
          ipl_type='alarm', pfd=0.1, justification='Separate sensor and sufficient response time assumed for the demo.')
        s('dd_sif', 'hse.sif', name='SIF-LAHH-201', description='Independent vessel high-high level shutdown',
          location_id=self.unit200, hazard_scenario='T-201 overfill and loss of containment.',
          target_safe_state='Close feed ESD valve; require authorized reset.', subsystem_sensor_type='level',
          required_sil='sil2', sensor_voting='1oo2', final_element_voting='1oo2',
          proof_test_interval_months=6, state='active')
        s('dd_sif_demand', 'hse.sif.demand', sif_id=r('dd_sif'), demand_date=self.time(-9),
          demand_type='proof_test', trip_cause='Scheduled full-loop proof test (synthetic).',
          actuation_time_seconds=1.4, success=True, notes='Feed isolated within the demo performance target.')
        for xmlid, tag, name, group, health, state in [
            ('dd_sece_esd', 'ESDV-201', 'T-201 feed emergency shutdown valve', 'emergency_shutdown', 'healthy', 'active'),
            ('dd_sece_detector', 'GD-114', 'Unit-100 flammable gas detection', 'detection', 'degraded', 'active'),
        ]:
            s(xmlid, 'hse.sece', tag=tag, name=name, location_id=self.unit200 if 'esd' in xmlid else self.unit100,
              asset_id=r('dd_asset_reactor') if 'esd' in xmlid else r('dd_asset_vessel'),
              sece_group=group, major_accident_hazard='Flammable hydrocarbon release and escalation.',
              functionality_std='Detect or isolate the hazard within the approved response time.',
              survivability_std='Maintain function under the defined fire and environmental design conditions.',
              barrier_health=health, state=state, next_ivb_audit_date=self.date(60))
        s('dd_sece_assurance', 'hse.sece.assurance', sece_id=r('dd_sece_esd'), test_date=self.date(-9),
          inspector_id=r('dd_user_presenter'), test_type='proof_test',
          test_procedure_ref='DEMO-SIS-201 Rev B', measured_parameters='Measured closure time: 1.4 seconds.', result='pass')
        s('dd_barrier_esd', 'hse.barrier.element', name='T-201 independent shutdown barrier',
          location_id=self.unit200, sece_id=r('dd_sece_esd'), sif_id=r('dd_sif'), health_status='effective')
        s('dd_barrier_inhibit', 'hse.barrier.element', name='LSL-2291 transmitter protection under authorized inhibit',
          location_id=self.unit200, health_status='bypassed',
          impairment_reason='Transmitter replacement under approved bypass request.',
          compensatory_measures='Dedicated watch, hourly level check and reduced throughput.')
        s('dd_pse_event', 'hse.pse', title='Small seal release contained inside Unit-100 bund',
          location_id=self.unit100, event_datetime=self.time(-7), tier='tier2',
          chemical_id=r('dd_chemical_benzene'), chemical_name='Hydrocarbon mixture (demo)',
          mass_released_kg=25, threshold_quantity_kg=20,
          barrier_failure_summary='Primary seal degraded; bund and operator containment response remained effective.',
          state='classified')
        s('dd_dispersion', 'hse.dispersion.scenario', name='Illustrative benzene release sensitivity study',
          location_id=self.unit100, sds_id=r('dd_sds_benzene'), chemical_name='Benzene',
          molecular_weight=78.11, boiling_point_c=80.1, vapor_pressure_kpa=12.7,
          release_phase='liquid', release_type='continuous_plume', release_rate_kg_s=0.5,
          total_mass_kg=100, wind_speed_m_s=3.0, stability_class='d', state='modeled',
          shelter_in_place_instructions='Training model only, not validated QRA. Use the approved emergency plan for actual decisions.')
        for i, discipline in enumerate(['process_safety', 'operations', 'electrical_instrument'], 1):
            s('dd_moc_review_%s' % i, 'hse.moc.review', moc_id=r('dd_moc_1'),
              discipline=discipline, reviewer_id=r('dd_user_presenter'),
              recommendation='approve_conditions', review_comments='Complete proof testing and update drawings before startup.')
        # Separate PSSR exercise: eight verified items and one open training item.
        s('dd_moc_pssr', 'hse.moc', title='T-201 transmitter replacement · PSSR readiness exercise',
          location_id=self.unit200, asset_id=r('dd_asset_reactor'), category='instrumentation',
          description_of_change='Commission the replacement level instrument after multidisciplinary review.',
          justification='Improve measurement reliability and reduce nuisance trips.', state='pssr')
        pssr_items = [
            ('engineering', 'Installation matches approved drawing'),
            ('engineering', 'Material and pressure-test evidence complete'),
            ('safety_systems', 'Relief and discharge paths inspected'),
            ('safety_systems', 'ESD and SIS full-loop tests witnessed'),
            ('procedures', 'Operating procedure revision approved'),
            ('procedures', 'Emergency procedure reviewed'),
            ('training', 'Night-shift familiarization complete'),
            ('environmental', 'Containment and drains inspected'),
            ('safety_systems', 'De-isolation clearance verified'),
        ]
        for i, (category, label) in enumerate(pssr_items, 1):
            verified = category != 'training'
            s('dd_pssr_%s' % i, 'hse.moc.pssr.line', moc_id=r('dd_moc_pssr'),
              category=category, item_description=label, is_verified=verified,
              verified_by=r('dd_user_presenter') if verified else False,
              verification_date=self.date(-1) if verified else False,
              notes='Evidence reviewed (synthetic)' if verified else 'Open: night-shift familiarization scheduled tomorrow')

    def _environment_and_health(self):
        s, r = self.seed, self.ref
        for key, point, fuel, status, exceed in [
            ('boiler', 'B-201 boiler stack', 180000, 'verified', False),
            ('flare', 'FL-101 flare — transient event', 25000, 'calculated', True),
        ]:
            s('dd_air_' + key, 'hse.env.air.emission', location_id=self.unit100,
              emission_point=point, reporting_date=self.date(-2), fuel_type='Natural gas',
              fuel_consumed=fuel, fuel_unit='scf', source_type='flare' if exceed else 'stationary_combustion',
              nox_kg=12.5, permit_limit_exceeded=exceed,
              exceedance_notes='Illustrative event: investigate duration and validate against the site-specific permit.' if exceed else False,
              state=status)
        for key, ph, oil, status in [('normal', 7.2, 2.5, 'compliant'), ('exceedance', 9.8, 14, 'exceedance')]:
            s('dd_water_' + key, 'hse.env.water.monitoring', location_id=self.unit100,
              outfall_number='DEMO-OUTFALL-002', sample_datetime=self.time(-2 if key == 'normal' else -1),
              lab_reference='DEMO-LAB-' + key.upper(), ph_level=ph, oil_grease_mg_l=oil, state=status)
        s('dd_waste', 'hse.env.waste.manifest', name='DEMO-WM-0001', location_id=self.warehouse,
          generator_epa_id='DEMO-GENERATOR-NOT-A-REAL-ID', waste_description='Spent solvent from maintenance cleaning',
          epa_waste_codes='DEMO D001/F003', container_count=4, total_quantity=640,
          accumulation_start_date=self.date(-78), transporter_company='Fictional GreenCycle Services',
          transporter_epa_id='DEMO-TRANSPORTER', tsdf_facility_name='Fictional Solvent Recovery Center',
          tsdf_epa_id='DEMO-TSDF', management_method='recycling')
        s('dd_spill', 'hse.env.spill', title='25 L seal leak · recovered inside concrete bund',
          location_id=self.unit100, spill_datetime=self.time(-7), substance_name='Hydrocarbon mixture (demo)',
          spill_source='equipment_seal', volume_released=25, volume_recovered=24,
          containment_measures='Isolate pump, protect drains and recover with absorbents.',
          remediation_plan='Dispose of absorbents using the linked demo waste process and verify the bund clean.',
          state='remediated')
        s('dd_esg', 'hse.esg.accounting', location_id=self.unit100, reporting_year=self.today.year,
          reporting_period='annual', state='internal_review',
          scope1_fuel_gas_tonnes=12500, scope1_diesel_tonnes=850,
          scope1_flaring_tonnes=3200, scope1_fugitive_tonnes=450,
          electricity_consumed_mwh=45000, renewable_energy_recs_mwh=15000,
          production_output_tonnes=250000)
        for key, tag, leaking in [('leak', 'XV-104 packing gland', True), ('normal', 'FV-118 flange', False)]:
            s('dd_ldar_' + key, 'hse.ldar.component', tag_number=tag, location_id=self.unit100,
              component_type='valve' if leaking else 'flange', leak_threshold_ppm=500, is_leaking=leaking)
            s('dd_ldar_reading_' + key, 'hse.ldar.reading', component_id=r('dd_ldar_' + key),
              inspection_date=self.date(-2), inspector_name='John Dsouza (demo technician)',
              snid_analyzer_serial='DEMO-FID-011', background_ppm=5,
              screening_value_ppm=1250 if leaking else 75)
        s('dd_seg', 'hse.ih.seg', name='Unit-100 maintenance and sampling team', code='SEG-CU100-01',
          location_id=self.unit100, job_description='Closed sampling, seal maintenance and line inspection.', worker_count=12)
        for key, concentration in [('normal', 0.2), ('overexposure', 1.5)]:
            s('dd_ih_' + key, 'hse.ih.sample', seg_id=r('dd_seg'), employee_id=r('dd_emp_john'),
              sample_date=self.date(-5), agent_name='Benzene (illustrative limits)',
              measured_concentration=concentration, sampling_duration_minutes=480,
              osha_pel=1.0, acgih_tlv=0.5,
              corrective_control='Review closed sampling and local extraction; limits are demo inputs, not regulatory advice.')
        s('dd_audiometry_baseline', 'hse.ih.audiometry', employee_id=r('dd_emp_bilal'),
          test_date=self.date(-365), test_type='baseline', audiologist_name='Fictional Occupational Health Clinic',
          l_2000=10, l_3000=10, l_4000=10, r_2000=10, r_3000=10, r_4000=10)
        s('dd_audiometry', 'hse.ih.audiometry', employee_id=r('dd_emp_bilal'),
          test_date=self.date(-14), audiologist_name='Fictional Occupational Health Clinic',
          baseline_audiogram_id=r('dd_audiometry_baseline'),
          l_2000=25, l_3000=25, l_4000=30, r_2000=12, r_3000=15, r_4000=15,
          recommendations='Synthetic threshold-shift example; refer for clinical review and hearing-protection reassessment.')
        s('dd_respirator', 'hse.ih.respirator', employee_id=r('dd_emp_john'),
          fit_test_date=self.date(-340), next_due_date=self.date(25),
          manufacturer_model='Demo full-face respirator, model FF-01', quantitative_fit_factor=1250)
        s('dd_ergonomics', 'hse.ih.ergonomics', job_task_name='Manual drum positioning at warehouse decant station',
          location_id=self.warehouse, reba_score=10, assessment_date=self.date(-12),
          remedial_measures='Replace manual movement with an approved trolley; see linked continuous improvement story.')
        s('dd_biological', 'hse.ih.biological.monitoring', employee_id=r('dd_emp_john'),
          chemical_agent='benzene_spma', sample_date=self.date(-5), measured_value=32,
          bei_limit=25, state='elevated',
          occupational_physician_notes='Entirely synthetic. Occupational physician review and repeat sampling required.')
        s('dd_radiation', 'hse.ih.radiation.dosimetry', employee_id=r('dd_emp_bilal'),
          tld_badge_number='DEMO-TLD-021', year=self.today.year,
          monitoring_period='q3', deep_dose_hp10_msv=0.45)

    def _control_of_work(self):
        s, r = self.seed, self.ref
        s('dd_loto_cse', 'hse.loto.plan', title='V-101 positive isolation · verified entry boundary',
          location_id=self.unit100, asset_id=r('dd_asset_vessel'),
          system_description='Inlet/outlet blinds, drained process inventory and isolated auxiliaries.',
          energy_chemical=True, energy_electrical=True, zero_energy_verified=True,
          zero_energy_verified_by=r('dd_user_presenter'), zero_energy_verified_date=self.time(-1),
          master_lockbox_no='DEMO-LB-101', state='isolated')
        for i, (tag, kind) in enumerate([('V101-IN-BLIND', 'blind_installed'), ('V101-AUX-MCC', 'breaker_open')], 1):
            s('dd_cse_isolation_%s' % i, 'hse.loto.point', plan_id=r('dd_loto_cse'),
              sequence=i * 10, point_identifier=tag, isolation_type=kind,
              lock_number='DEMO-LOCK-%s' % i, tag_number='DEMO-TAG-%s' % i,
              applied_by='John Dsouza', verified_by='Elena Morris')
        s('dd_cse', 'hse.permit.confined.space', permit_id=r('dd_ptw_cse'),
          location_id=self.unit100, space_identifier='V-101 slug catcher',
          loto_plan_id=r('dd_loto_cse'), isolation_verified=True, electrical_lockout_verified=True,
          attendant_name='Alex Morgan (fictional contractor)', state='active_entry')
        s('dd_cse_entrant', 'hse.permit.cs.entrant', cse_id=r('dd_cse'),
          worker_name='John Dsouza', badge_number='DEMO-EMP-003', entry_time=self.time(hours=-0.5))
        s('dd_cse_exited', 'hse.permit.cs.entrant', cse_id=r('dd_cse'),
          worker_name='Bilal Ahmed', badge_number='DEMO-EMP-004',
          entry_time=self.time(hours=-1), exit_time=self.time(hours=-0.25), status='exited')
        for i, o2 in enumerate([20.9, 20.8, 20.9], 1):
            s('dd_cse_gas_%s' % i, 'hse.permit.cs.gas_log', cse_id=r('dd_cse'),
              sample_timestamp=self.time(hours=-0.75 + i * 0.2), oxygen_pct=o2,
              combustible_lel_pct=0, h2s_ppm=0, co_ppm=1)
        s('dd_prep', 'hse.preparation.activity', title='V-101 inspection readiness package',
          location_id=self.unit100, asset_id=r('dd_asset_vessel'), scheduled_date=self.date(),
          activity_type='confined_prep', permit_id=r('dd_ptw_cse'), loto_plan_id=r('dd_loto_cse'),
          gate1_planning=True, gate2_isolation=True, gate3_site_prep=True, gate4_ready=False,
          state='gate_review')
        for i, (category, label, done) in enumerate([
            ('blinding', 'Verify blind register and lockbox', True),
            ('ventilation', 'Install continuous forced ventilation', True),
            ('lighting', 'Inspect low-voltage task lighting', True),
            ('waste', 'Final area walkdown and waste staging', False),
        ], 1):
            s('dd_prep_task_%s' % i, 'hse.preparation.task', activity_id=r('dd_prep'),
              task_category=category, name=label, is_completed=done, responsible_person='John Dsouza')
        for xmlid, title, permit_type, loc in [
            ('dd_ptw_lift', 'R-201 exchanger replacement lift', 'cold_work', self.unit200),
            ('dd_ptw_excavation', 'Warehouse firewater line trench', 'excavation', self.warehouse),
            ('dd_ptw_ndt', 'Night-shift weld inspection exclusion zone', 'radiography', self.unit200),
        ]:
            s(xmlid, 'hse.permit', title=title, permit_type=permit_type, location_id=loc,
              work_order_ref='DEMO-' + xmlid.upper(),
              start_datetime=self.time(1), end_datetime=self.time(2), state='draft')
        s('dd_lift', 'hse.permit.critical.lift', title='R-201 exchanger lift · 82.5% crane utilization',
          permit_id=r('dd_ptw_lift'), location_id=self.unit200, crane_model='Demo mobile crane C-300',
          crane_capacity_tonnes=300, boom_length_meters=40, operating_radius_meters=18,
          net_load_weight_tonnes=48, rigging_tackle_weight_tonnes=1.5, rated_capacity_at_radius=60,
          rigging_engineer_id=r('dd_user_presenter'), crane_operator_id=self.owner, state='approved')
        s('dd_excavation', 'hse.permit.excavation', title='Firewater line trench · utility clearance',
          permit_id=r('dd_ptw_excavation'), location_id=self.warehouse,
          expected_completion=self.date(7), call_811_ticket_number='DEMO-UTILITY-001',
          competent_person_id=r('dd_user_presenter'), excavation_depth_m=1.8,
          protective_system='trench_box', state='inspected')
        s('dd_radiography', 'hse.permit.radiography', title='Unit-200 spool weld inspection',
          permit_id=r('dd_ptw_ndt'), location_id=self.unit200, shoot_datetime=self.time(1, 8),
          source_serial_no='DEMO-NDT-SOURCE-001', radiation_protection_officer_id=r('dd_user_presenter'),
          radiographer_name='Fictional NDT Technician', state='approved')
        s('dd_simops_rule', 'hse.simops.matrix', activity_type_a='hot_work', activity_type_b='confined_space',
          compatibility='prohibited', min_separation_distance_m=30,
          mitigation_required='Do not execute concurrently in the same exclusion zone. Reschedule and obtain site authorization.')
        for key, name, source, x, y, permit in [
            ('hot', 'Flare drain hot work', 'hot_work', 100, 100, 'dd_ptw_hot'),
            ('entry', 'V-101 confined-space entry', 'confined_space', 115, 108, 'dd_ptw_cse'),
        ]:
            s('dd_radar_' + key, 'hse.simops.radar.plot', name=name, location_id=self.unit100,
              grid_zone='CU100-DEMO-GRID-A', coord_x=x, coord_y=y, hazard_radius_m=25,
              source_type=source, permit_id=r(permit))

    def _emergency_and_contractors(self):
        s, r = self.seed, self.ref
        s('dd_emergency_plan', 'hse.emergency.plan', title='Unit-100 hydrocarbon release response · training plan',
          location_id=self.unit100, incident_commander_id=r('dd_user_presenter'), deputy_commander_id=self.owner,
          emergency_type='hydrocarbon_fire',
          response_actions='TRAINING ONLY: alarm, stop work, isolate if safe, muster upwind, coordinate with incident command.',
          internal_callout_list='Demo incident commander → ERT → operations coordinator → occupational health.',
          external_agencies='Fictional municipal fire and hospital contacts. No live dispatch or notification integration.',
          muster_stations='Muster Alpha (primary); Muster Bravo (alternate upwind location).')
        s('dd_emergency_drill', 'hse.emergency.drill', plan_id=r('dd_emergency_plan'),
          title='Full-site evacuation exercise · one unaccounted badge', drill_date=self.date(-10),
          alarm_activation_time=self.time(-10), all_clear_time=self.time(-10, 0.5),
          total_personnel_on_site=120, total_personnel_mustered=119,
          strengths_observed='ERT on scene in 3.5 minutes; radio discipline maintained.',
          areas_for_improvement='One contractor badge missing from rollcall; reconcile gate roster and complete corrective action.',
          drill_score_percent=86, state='critiqued')
        for xmlid, name, employee, role, call in [
            ('dd_ert_elena', 'Elena Morris', 'dd_emp_elena', 'incident_commander', 'IC-01'),
            ('dd_ert_ahmed', 'Ahmed Raza', 'dd_emp_ahmed', 'fire_team_leader', 'FIRE-01'),
            ('dd_ert_john', 'John Dsouza', 'dd_emp_john', 'search_rescue', 'RESCUE-01'),
        ]:
            s(xmlid, 'hse.emergency.team', name=name, employee_id=r(employee), role=role,
              phone='DEMO ONLY — no live telephone', radio_call_sign=call)
        for key, worker, days, state in [('active', 'Alex Morgan', 320, 'active'),
                                         ('expired', 'Taylor Reed', -5, 'expired')]:
            s('dd_induction_' + key, 'hse.contractor.induction', contractor_id=r('dd_contract_alpha'),
              worker_name=worker, national_id_passport='DEMO-FICTIONAL-ID-' + key.upper(),
              job_title='Mechanical inspection technician', induction_date=self.date(-45),
              expiry_date=self.date(days), state=state)
        s('dd_contractor_kpi', 'hse.contractor.kpi', contractor_id=r('dd_contract_alpha'),
          year=self.today.year, month=str(self.today.month), man_hours_worked=18000,
          toolbox_talks_conducted=36, safety_inspections_count=8, near_misses_count=3)
        s('dd_drill_action', 'hse.action', title='Reconcile contractor gate roster before every evacuation drill',
          description='Align induction badges, shift attendance and muster roll; verify at the next exercise.',
          source_type='other', source_reference='Emergency evacuation exercise',
          assigned_to=r('dd_user_presenter'), target_date=self.date(5), state='assigned', priority='2')
        s('dd_portal_observation', 'observation.observation',
          employee_observer_name='Alex Morgan', employee_code='DEMO-CON-001',
          location_id=self.unit100, hazard_type='physical', priority='2',
          observation='Air hose crosses the marked route to Muster Alpha.',
          immediate_action='Rerouted hose and informed the area supervisor.', state='draft')
        s('dd_portal_incident', 'incident.reporting', incident_type='near_miss',
          incident_date=self.date(-1), select_emp_type='external',
          external_company_name='Alpha Industrial Services Co. (fictional)', external_employee_name='Alex Morgan',
          location_profile_id=self.unit100, exact_location='V-101 inspection access route',
          ir_description='Trip avoided at the inspection staging area.',
          incident_detail='Loose staging strap identified and removed before personnel entered the route.',
          summary_of_incident='Contractor near-miss report · no injury', state='draft')

    def _governance_and_reliability(self):
        s, r = self.seed, self.ref
        s('dd_compliance_audit', 'hse.compliance.audit', title='Mechanical integrity evidence sample review',
          regulation_id=r('dd_reg_osha_psm'), location_id=self.unit100, audit_date=self.date(-15),
          score_percentage=86, findings_count=2, state='action_tracking',
          findings_summary='Certification expiry and isolation evidence gaps; fictional regulatory assessment.')
        s('dd_financial_loss', 'hse.benefit.loss', title='K-301 bearing failure · downtime and repair cost',
          event_type='loss', location_id=self.unit100, asset_id=r('dd_asset_compressor'),
          event_date=self.date(-7), downtime_hours=8, loss_production_cost=64000,
          loss_equipment_repair=18000, loss_contractor_services=4500, state='verified',
          notes='Illustrative USD-equivalent figures; not posted to an accounting ledger.')
        s('dd_financial_benefit', 'hse.benefit.loss', title='Mechanical drum handling · annual avoided cost',
          event_type='benefit', location_id=self.warehouse, improvement_id=r('dd_impr_drums'),
          benefit_cost_avoidance=18000, benefit_safety_roi=6500, state='verified',
          notes='Synthetic business-case estimate; validate assumptions with the client.')
        s('dd_operator_event', 'hse.operator.log.entry', log_id=r('dd_oplog_1'),
          category='maintenance', priority='medium', asset_id=r('dd_asset_vessel'),
          description='V-101 entry active. Check entrant register and preserve isolation at handover.')
        s('dd_operator_round', 'hse.operator.log.round', log_id=r('dd_oplog_1'),
          asset_id=r('dd_asset_compressor'), parameter_name='Drive-end bearing temperature',
          recorded_value=92, unit_of_measure='°C', min_limit=40, max_limit=85)
        s('dd_operator_alarm', 'hse.operator.log.alarm', log_id=r('dd_oplog_1'),
          tag_number='TAH-K301', description='Compressor bearing high-temperature alarm',
          status='standing', priority='high', reason='Awaiting bearing/cooler maintenance review.',
          compensating_measure='Hourly temperature and vibration rounds; follow the approved operating limits.')
        for employee in ['dd_emp_ahmed', 'dd_emp_sara', 'dd_emp_john']:
            s('dd_ack_' + employee, 'hse.policy.acknowledgment', policy_id=r('dd_pol_001'),
              employee_id=r(employee), digital_signature='DEMO-ACKNOWLEDGMENT-NOT-A-LEGAL-SIGNATURE')
        for i, (label, details, hold) in enumerate([
            ('Verify work authorization', 'Confirm permit scope, JSA briefing and assigned authorities.', True),
            ('Establish positive isolation', 'Verify locks, blinds and a witnessed zero-energy check against the approved scheme.', True),
            ('Control the line opening', 'Apply containment and the approved opening sequence; stop if conditions differ.', False),
            ('Inspect and hand back', 'Check area, tools and personnel before authorized return to service.', True),
        ], 1):
            s('dd_sop_step_%s' % i, 'hse.operating.procedure.step', procedure_id=r('dd_sop_014'),
              step_number=i, name=label, detailed_instructions=details, is_hold_point=hold,
              hazard_warning='Illustrative only — follow the approved site procedure.',
              verification_check='Authorized witness records acceptance at each hold point.')
        for i, competency in enumerate(['dd_comp_agt', 'dd_comp_ptw'], 1):
            s('dd_role_comp_%s' % i, 'hse.role.competency', job_id=r('dd_job_operator'),
              competency_id=r(competency), minimum_level='level3')

    def _enrich_existing_scenarios(self):
        """One-time linkage of the original XML samples; preserve later user edits."""
        if self.env.ref('hse_demo_data.dd_enrichment_marker', raise_if_not_found=False):
            return
        r = self.ref
        updates = {
            'dd_loc_unit100': {'parent_id': r('dd_plant'), 'manager_id': r('dd_user_presenter')},
            'dd_loc_unit200': {'parent_id': r('dd_plant'), 'manager_id': r('dd_user_presenter')},
            'dd_loc_wh': {'parent_id': r('dd_plant')},
            'dd_swa_1': {'supervisor_id': r('dd_emp_ahmed'), 'rule_id': r('hse.lsr_line_of_fire')},
            'dd_emp_sara': {'gender': 'female', 'birthday': '1991-06-17', 'mobile_phone': '+1 202-555-0142'},
            'dd_emp_ahmed': {'gender': 'male', 'birthday': '1986-05-08', 'mobile_phone': '+1 202-555-0101'},
            'dd_emp_john': {'gender': 'male', 'birthday': '1988-09-03', 'mobile_phone': '+1 202-555-0183'},
            'dd_emp_bilal': {'gender': 'male', 'birthday': '1993-02-12', 'mobile_phone': '+1 202-555-0171'},
            'dd_inv_lti1': {'investigation_leader': r('dd_emp_elena'),
                            'team_members': [Command.set([r('dd_emp_elena'), r('dd_emp_john'), r('dd_emp_ahmed')])],
                            'assigned_to': r('dd_user_presenter'),
                            'location': r('dd_legacy_unit100'),
                            'person_impacted': r('dd_emp_sara'),
                            'select_department': r('dd_dept_operations'),
                            'responsible_person': r('dd_user_presenter'),
                            'role_in_incident': 'Process operator assisting guard repositioning after a maintenance interruption.',
                            'inv_conclusion': '<p>The event followed an undefined interruption/restart hold point. Strengthen isolation re-verification, handover ownership and field assurance. Fictional investigation only.</p>'},
            'dd_inc_lti1': {'person_impacted': r('dd_emp_sara'),
                           'location': r('dd_legacy_unit100'),
                           'select_department': r('dd_dept_operations'),
                           'responsible_person': r('dd_user_presenter'),
                           'assigned_to': r('dd_user_presenter'),
                           'incident_report_date': self.time(-24), 'reported_date': self.date(-24),
                           'select_body_part': r('dd_body_hand'),
                           'injury_create_level': r('dd_grade_lti'),
                           'category_id': r('dd_inc_category'),
                           'select_severity_level': r('dd_severity_major'),
                           'role_in_incident': 'Process operator assisting guard repositioning after an interruption.',
                           'task_performed': 'Reposition compressor coupling guard',
                           'date_of_injury': self.date(-24), 'time_of_injury': self.time(-24),
                           'time_employee_started_work': 7.0, 'body_part': 'arm', 'injury_category': 'fracture',
                           'employee_activity_before_incident': '<p>Assisting guard alignment during maintenance at K-301.</p>',
                           'directly_harmed_the_employee': '<p>Unexpected coupling movement at an accessible pinch point.</p>',
                           'describe_the_injury': '<p>Synthetic right-hand crush injury used to illustrate the reporting workflow.</p>',
                           'injury_illness': 'injury?', 'treatement_provider': 'outside',
                           'physician_name': 'Dr. H. Qureshi (fictional)',
                           'facility_name': 'City Occupational Health Clinic (fictional)',
                           'city': 'Northstar Demo City', 'phone': '+1 202-555-0190',
                           'email': 'clinic@northstar.example', 'post_treatment': '3',
                           'treatment_provided': 'First aid followed by a fictional occupational-health assessment.',
                           'person_treatment': 'Twelve days away followed by five days of restricted duties.',
                           'no_of_days': 12, 'restricted_area': 'No rotating-equipment work during the illustrative restriction period.',
                           'precautions_description': 'Stop work, secure equipment, preserve the scene and arrange assessment.'},
            'dd_ra_1': {'analysis': r('dd_analysis'), 'team_lead_ids': r('dd_emp_elena'),
                         'location': r('dd_legacy_unit200')},
            'dd_jsa_1': {'analysis': r('dd_analysis'), 'team_lead_ids': r('dd_emp_john'),
                          'location': r('dd_legacy_unit100')},
            'dd_hazard_restart': {'corrective_id': r('dd_legacy_capa')},
            'dd_hazard_dropped': {'preventive_id': r('dd_legacy_preventive')},
            'dd_ptw_cse': {'risk_assessment_id': r('dd_jsa_1'), 'loto_plan_id': r('dd_loto_cse'),
                           'req_lockout': True, 'req_hole_watch': True,
                           'simops_authorized_by': r('dd_user_presenter'),
                           'simops_mitigation': 'Separate work fronts and timings; dedicated coordinator authorization (demo).'},
            'dd_ptw_hot': {'risk_assessment_id': r('dd_jsa_1')},
            'dd_loto_k301': {'asset_id': r('dd_asset_compressor'), 'zero_energy_verified': True,
                             'zero_energy_verified_by': r('dd_user_presenter'), 'zero_energy_verified_date': self.time(-1)},
            'dd_moc_1': {'asset_id': r('dd_asset_reactor'), 'estimated_cost': 42000},
            'dd_moc_2': {'temporary_expiry_date': self.date(42), 'reversion_plan': 'Remove temporary feed and restore the certified permanent board.'},
            'dd_ncr_1': {'location_id': self.unit100, 'asset_id': r('dd_asset_vessel'),
                         'is_quarantined': True, 'quarantine_tag_no': 'DEMO-NCR-Q-001',
                         'quarantine_location': 'Warehouse quarantine bay',
                         'immediate_containment_action': 'Segregated material; do not install until traceability is verified.'},
            'dd_capa_1': {'assigned_to': r('dd_user_presenter'), 'investigation_id': r('dd_inv_lti1'),
                          'incident_id': r('dd_inc_lti1')},
            'dd_oplog_1': {'relieving_operator_id': r('dd_user_presenter'),
                           'handover_standing_orders': 'Review V-101 entrants, active permits, K-301 bearing temperature and open actions.'},
            'dd_portal_observation': {'create_uid': r('dd_user_contractor')},
            'dd_portal_incident': {'create_uid': r('dd_user_contractor')},
        }
        for xmlid, days, dept in [('dd_inc_lti0', -380, 'dd_dept_maintenance'),
                                   ('dd_inc_nm', -3, 'dd_dept_operations'),
                                   ('dd_inc_fire', -9, 'dd_dept_operations'),
                                   ('dd_inc_transport', -1, 'dd_dept_warehouse')]:
            updates.setdefault(xmlid, {}).update({
                'responsible_person': r('dd_user_presenter'), 'assigned_to': r('dd_user_presenter'),
                'select_department': r(dept), 'incident_report_date': self.time(days),
                'reported_date': self.date(days),
            })
        updates['dd_inc_lti0']['person_impacted'] = r('dd_emp_bilal')
        updates['dd_obs_1'] = {'observer_id': r('dd_user_presenter'),
                                'responsible_person': r('dd_user_presenter'),
                                'responsible_user_id': r('dd_user_presenter'),
                                'select_department': r('dd_dept_operations'),
                                'hazard_photo_filename': 'northstar-coupling-demo.png'}
        with tools.file_open('hse_demo_data/static/demo/blocked_walkway.png', 'rb') as evidence:
            photo = base64.b64encode(evidence.read())
        with tools.file_open('hse_demo_data/static/demo/unguarded_coupling.png', 'rb') as evidence:
            updates['dd_obs_1']['hazard_photo'] = base64.b64encode(evidence.read())
        updates['dd_portal_observation']['hazard_photo'] = photo
        updates['dd_portal_observation']['hazard_photo_filename'] = 'northstar-walkway-demo.png'
        for xmlid, values in updates.items():
            self.env.ref('hse_demo_data.' + xmlid).with_context(tracking_disable=True).write(values)
        # Refresh both sides after all overlapping permits have been linked.
        permits = self.env['hse.permit'].browse([r('dd_ptw_hot'), r('dd_ptw_cse')])
        permits._compute_simops()
        # A commissioned sample should show complete evidence, not a blank PSSR.
        moc = self.env.ref('hse_demo_data.dd_moc_2')
        moc.action_load_default_pssr()
        moc.pssr_line_ids.write({'is_verified': True, 'verified_by': r('dd_user_presenter'),
                                 'verification_date': self.date(-2)})
        self.seed('dd_enrichment_marker', 'ir.config_parameter',
                  key='hse_demo_data.comprehensive_seed_date', value=str(self.today))
