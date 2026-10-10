"""Client-demo coverage, connected evidence, genuine gates and upgrade safety."""
import ast
import base64
import xml.etree.ElementTree as ElementTree
from types import SimpleNamespace
from unittest.mock import patch

from odoo import tools
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.hse.controllers import hse_dashboard_controller

from ..demo_catalog import CATEGORIES, MODULES, REPORTS, SCENARIOS
from ..services import build_demo_context, build_walkthrough
from ..models.preview_http import preview_cookie_scope, partition_session_cookies
from werkzeug.wrappers import Response


@tagged('post_install', '-at_install')
class TestHSEClientDemo(TransactionCase):
    def sample(self, name):
        return self.env.ref(name if '.' in name else 'hse_demo_data.' + name)

    def test_catalog_is_complete_and_presenter_can_read_it(self):
        presenter = self.sample('dd_user_presenter')
        context = build_demo_context(self.env(user=presenter))
        self.assertEqual(len(CATEGORIES), 14)
        self.assertEqual(len(MODULES), 73)
        self.assertEqual(len(SCENARIOS), 8)
        self.assertEqual(len(REPORTS), 10)
        self.assertEqual(context['issues'], [])
        self.assertEqual(context['ready_count'], context['module_count'])
        self.assertGreaterEqual(context['record_count'], 150)
        self.assertEqual(context['journey_minutes'], 80)
        guide = build_walkthrough(context)
        for scenario in SCENARIOS:
            self.assertIn(scenario['title'], guide)
        for module in MODULES:
            self.assertIn(module['sample'], guide)
        self.assertIn('does not enforce', guide)

    def test_every_native_business_menu_has_populated_records(self):
        root = self.env.ref('hse.menu_hse_root')
        menus = self.env['ir.ui.menu'].search([('id', 'child_of', root.id)])
        seen = set()
        for menu in menus:
            action = menu.action
            if not action or action._name != 'ir.actions.act_window':
                continue
            model = self.env[action.res_model]
            if model._transient or action.res_model.endswith('.wizard'):
                continue
            seen.add(action.res_model)
            self.assertGreater(model.search_count([]), 0,
                               'Empty business menu: %s (%s)' % (menu.name, action.res_model))
        self.assertGreaterEqual(len(seen), 65)

    def test_xml_relation_references_match_the_actual_field_models(self):
        # A user ID can accidentally match an unrelated employee ID on one
        # database and then fail on the next. Validate the *model*, not the ID.
        with tools.file_open('hse_demo_data/__manifest__.py') as source:
            manifest = ast.literal_eval(source.read())
        for filename in manifest['data']:
            if not filename.endswith('.xml'):
                continue
            with tools.file_open('hse_demo_data/' + filename) as source:
                root = ElementTree.parse(source)
            for record in root.findall('.//record'):
                model = self.env[record.get('model')]
                for field in record.findall('field'):
                    if not field.get('ref'):
                        continue
                    definition = model._fields[field.get('name')]
                    if definition.type not in ('many2one', 'many2many'):
                        continue
                    target = self.sample(field.get('ref'))
                    self.assertEqual(definition.comodel_name, target._name,
                                     '%s: %s.%s -> %s' % (filename, record.get('id'),
                                                          field.get('name'), field.get('ref')))

    def test_featured_incident_details_and_synthetic_evidence_are_complete(self):
        incident = self.sample('dd_inc_lti1')
        self.assertEqual(incident.person_impacted, self.sample('dd_emp_sara'))
        self.assertEqual(incident.select_department, incident.person_impacted.department_id)
        self.assertEqual(incident.responsible_person, self.sample('dd_user_presenter'))
        self.assertTrue(incident.incident_report_date)
        self.assertTrue(incident.rel_email.endswith('.example'))
        self.assertTrue(incident.role_in_incident)
        self.assertTrue(incident.describe_the_injury)
        self.assertIn('fictional', incident.physician_name)
        self.assertEqual(self.sample('dd_swa_1').supervisor_id, self.sample('dd_emp_ahmed'))
        self.assertEqual(len(self.sample('dd_inv_lti1').team_members), 3)
        for name in ('dd_obs_1', 'dd_portal_observation'):
            record = self.sample(name)
            self.assertTrue(base64.b64decode(record.hazard_photo).startswith(b'\x89PNG'))
            self.assertTrue(record.hazard_photo_filename.endswith('.png'))
        self.assertNotEqual(self.sample('dd_obs_1').hazard_photo,
                            self.sample('dd_portal_observation').hazard_photo)

    def test_featured_forms_and_journey_records_resolve(self):
        for definition in MODULES:
            record = self.sample(definition['sample'])
            action = self.env.ref(definition['action'])
            self.assertEqual(record._name, action.res_model)
            self.assertTrue(record.get_view(False, 'form').get('arch'), definition['title'])
        for scenario in SCENARIOS:
            for item in scenario['steps']:
                self.assertTrue(self.sample(item['record']).exists(), item['title'])

    def test_loader_is_idempotent_and_preserves_presenter_edits(self):
        hazop = self.sample('dd_hazop')
        hazop.title = 'Client-specific title edited during the demo'
        before = self.env['ir.model.data'].search_count([('module', '=', 'hse_demo_data')])
        self.env['hse.demo.loader'].load_comprehensive_demo()
        self.env['hse.demo.loader'].load_comprehensive_demo()
        after = self.env['ir.model.data'].search_count([('module', '=', 'hse_demo_data')])
        self.assertEqual(before, after)
        self.assertEqual(hazop.title, 'Client-specific title edited during the demo')
        self.assertEqual(len(self.sample('dd_moc_2').pssr_line_ids), 9)
        xid = self.env['ir.model.data'].search([
            ('module', '=', 'hse_demo_data'), ('name', '=', 'dd_hazop')])
        self.assertTrue(xid.noupdate)

    def test_incident_to_action_evidence_chain(self):
        incident, investigation, action = (self.sample(name) for name in
                                          ('dd_inc_lti1', 'dd_inv_lti1', 'dd_capa_1'))
        self.assertEqual(investigation.incident_id, incident)
        self.assertEqual(action.incident_id, incident)
        self.assertEqual(action.investigation_id, investigation)
        self.assertEqual(len(investigation.why_ids), 5)
        self.assertEqual(len(investigation.fishbone_ids), 6)
        self.assertEqual(len(investigation.timeline_ids), 4)
        self.assertEqual(len(investigation.bowtie_barrier_ids), 4)
        self.assertEqual(len(incident.event_ids), 4)
        self.assertTrue(incident.is_osha_recordable)
        self.assertTrue(investigation.why_ids.filtered('is_root_cause'))

    def test_hazop_lopa_moc_and_assurance_are_linked(self):
        deviation = self.sample('dd_hazop_deviation')
        recommendation = self.sample('dd_hazop_recommendation')
        self.assertEqual(self.sample('dd_lopa').hazop_deviation_id, deviation)
        self.assertEqual(recommendation.deviation_id, deviation)
        self.assertEqual(recommendation.moc_id, self.sample('dd_moc_1'))
        self.assertEqual(recommendation.action_id.moc_id, recommendation.moc_id)
        self.assertEqual(self.sample('dd_sif_demand').sif_id, self.sample('dd_sif'))
        self.assertEqual(self.sample('dd_sece_assurance').sece_id, self.sample('dd_sece_esd'))
        self.assertTrue(self.sample('dd_barrier_inhibit').is_impaired)

    def test_real_preparation_and_loto_clearance_gates(self):
        prep = self.sample('dd_prep')
        self.assertEqual(prep.readiness_progress, 75.0)
        with self.assertRaises(UserError):
            prep.action_authorize_ready()
        prep.gate4_ready = True
        prep.action_authorize_ready()
        self.assertEqual(prep.state, 'ready')
        loto = self.sample('dd_loto_cse')
        self.assertTrue(loto.zero_energy_verified)
        with self.assertRaises(UserError):
            loto.action_deisolate()
        loto.write({'deisolate_tools_cleared': True, 'deisolate_guards_replaced': True,
                    'deisolate_personnel_clear': True})
        loto.action_deisolate()
        self.assertEqual(loto.state, 'de-isolated')

    def test_real_simops_authorization_gate(self):
        permit = self.sample('dd_ptw_hot')
        permit.simops_authorized_by = False
        permit._compute_simops()
        self.assertTrue(permit.has_simops_conflict)
        self.assertEqual(permit.simops_risk_level, 'high')
        with self.assertRaises(UserError):
            permit.action_start_work()
        permit.simops_authorized_by = self.sample('dd_user_presenter')
        permit.action_start_work()
        self.assertEqual(permit.state, 'active')

    def test_real_confined_space_accountability_gate(self):
        cse = self.sample('dd_cse')
        self.assertEqual(cse.permit_id, self.sample('dd_ptw_cse'))
        self.assertEqual(cse.loto_plan_id, self.sample('dd_loto_cse'))
        self.assertEqual(cse.active_entrants_count, 1)
        self.assertTrue(cse.latest_atmosphere_safe)
        with self.assertRaises(ValidationError):
            cse.action_close_entry()
        cse.entrant_ids.filtered(lambda record: record.status == 'inside').action_log_exit()
        cse.action_close_entry()
        self.assertEqual(cse.state, 'closed')

    def test_pssr_verification_examples(self):
        pssr = self.sample('dd_moc_pssr')
        self.assertEqual(len(pssr.pssr_line_ids), 9)
        self.assertEqual(len(pssr.pssr_line_ids.filtered('is_verified')), 8)
        self.assertFalse(pssr.pssr_completed)
        pssr.pssr_line_ids.write({'is_verified': True})
        self.assertTrue(pssr.pssr_completed)
        self.assertTrue(self.sample('dd_moc_2').pssr_completed)

    def test_environment_health_and_emergency_exceptions(self):
        self.assertTrue(self.sample('dd_water_normal').is_compliant)
        self.assertFalse(self.sample('dd_water_exceedance').is_compliant)
        self.assertTrue(self.sample('dd_ih_overexposure').exceeds_pel)
        self.assertFalse(self.sample('dd_ih_normal').exceeds_pel)
        self.assertTrue(self.sample('dd_biological').exceeds_bei)
        self.assertTrue(self.sample('dd_audiometry').has_sts)
        self.assertTrue(self.sample('dd_ldar_reading_leak').is_leak)
        self.assertEqual(self.sample('dd_ldar_reading_leak').net_leak_ppm, 1245)
        self.assertFalse(self.sample('dd_ldar_reading_normal').is_leak)
        self.assertEqual(self.sample('dd_emergency_drill').unaccounted_personnel, 1)
        self.assertEqual(self.sample('dd_spill').recovery_percentage, 96)
        self.assertEqual(self.sample('dd_financial_loss').total_loss, 86500)
        self.assertEqual(self.sample('dd_financial_benefit').total_benefit, 24500)

    def test_risk_matrix_counts_use_the_actual_likelihood_field(self):
        controller = hse_dashboard_controller.HSEDashboardController()
        with patch.object(hse_dashboard_controller, 'request', SimpleNamespace(env=self.env)):
            data = controller._collect_dashboard_data()
        cells = [cell for row in data['matrix_grid'] for cell in row]
        self.assertEqual(len(cells), 25)
        self.assertEqual(sum(cell['count'] for cell in cells),
                         self.env['ra_jsa.hazard'].search_count([]))
        critical = next(cell for cell in cells if cell['consequence'] == 5 and cell['likelihood'] == 4)
        self.assertGreaterEqual(critical['count'], 1)
        self.assertEqual(data['barrier_health_pct'], 50.0)
        self.assertEqual(data['trir_source'], 'api_rp_754_metrics')

    def test_portal_samples_are_owned_and_loader_is_admin_only(self):
        portal = self.sample('dd_user_contractor')
        self.assertFalse(portal.has_group('base.group_user'))
        self.assertFalse(portal.has_group('hse_demo_data.group_demo_presenter'))
        self.assertEqual(self.sample('dd_portal_observation').create_uid, portal)
        self.assertEqual(self.sample('dd_portal_incident').create_uid, portal)
        for user in (portal, self.sample('dd_user_presenter')):
            with self.assertRaises(AccessError):
                self.env['hse.demo.loader'].with_user(user).load_comprehensive_demo()

    def test_embedded_preview_cookie_policy_is_narrow_and_preserves_http_only(self):
        self.assertFalse(preview_cookie_scope(False, 'https', 'https://8069-test.e2b.app'))
        self.assertFalse(preview_cookie_scope(True, 'http', 'http://8069-test.e2b.app'))
        self.assertFalse(preview_cookie_scope(True, 'https', 'https://client.example'))
        self.assertFalse(preview_cookie_scope(True, 'https', 'https://fake-e2b.app'))
        self.assertTrue(preview_cookie_scope(True, 'https', 'https://8069-test.e2b.app'))
        self.assertTrue(preview_cookie_scope(True, 'http', 'http://8069-test.e2b.app',
                                            'https://8069-test.e2b.app'))
        self.assertFalse(preview_cookie_scope(True, 'http', 'http://attacker.e2b.app',
                                             'https://8069-test.e2b.app'))
        response = Response('test')
        response.set_cookie('session_id', 'test-session', httponly=True)
        response.set_cookie('other', 'unchanged')
        original = response.headers.getlist('Set-Cookie')[1]
        partition_session_cookies(response)
        cookie, other = response.headers.getlist('Set-Cookie')
        self.assertIn('SameSite=None', cookie)
        self.assertIn('Secure', cookie)
        self.assertIn('Partitioned', cookie)
        self.assertIn('HttpOnly', cookie)
        self.assertIn('Path=/', cookie)
        self.assertEqual(other, original)

    def test_all_ten_featured_reports_render_from_seeded_data(self):
        presenter = self.sample('dd_user_presenter')
        for definition in REPORTS:
            record = self.sample(definition['record'])
            content, fmt = self.env['ir.actions.report'].with_user(presenter)._render_qweb_html(
                definition['action'], record.ids)
            self.assertEqual(fmt, 'html')
            self.assertGreater(len(content), 500, definition['title'])
