# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from unittest.mock import MagicMock, patch
from werkzeug.wrappers import Response as WerkzeugResponse
from odoo.addons.observation_portal.controllers import controllers

class TestObservationPortal(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ObsForm = cls.env['observation.form']
        cls.Obs = cls.env['observation.observation']
        cls.Location = cls.env['hse.location.profile']

        cls.loc = cls.Location.create({
            'name': 'Catalytic Reformer Unit (CRU-100)',
            'code': 'LOC-CRU-100',
        })

    def test_01_observation_form_model(self):
        form_rec = self.ObsForm.create({
            'name': 'John Worker',
            'email': 'john.worker@example.com',
            'observation': 'Missing handrail on stairs near tank 402',
            'user_id': self.env.user.id,
        })
        self.assertEqual(form_rec.name, 'John Worker')
        self.assertEqual(form_rec.email, 'john.worker@example.com')

    def test_02_portal_controller_submission_with_photo(self):
        controller = controllers.ObservationPortalController()
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.redirect.return_value = WerkzeugResponse("Redirect", status=302)

        # Mock photo upload file
        mock_photo = MagicMock()
        mock_photo.filename = 'hazard_sample.jpg'
        mock_photo.read.return_value = b'simulated_binary_image_data'
        mock_req.httprequest.files.get.return_value = mock_photo

        with patch.object(controllers, 'request', mock_req):
            controller.submit_form(
                name='Michael Scott',
                employee_code='BADGE-774',
                hazard_type='chemical',
                priority='3',
                observation='Unlabeled drum stored near stormwater drain',
                immediate_action='Placed absorbent spill boom around drain',
                location_id=str(self.loc.id),
            )
            self.assertTrue(mock_req.redirect.called)

        # Verify observation record created
        created_obs = self.Obs.search([('employee_code', '=', 'BADGE-774')], limit=1)
        self.assertTrue(created_obs)
        self.assertEqual(created_obs.employee_observer_name, 'Michael Scott')
        self.assertEqual(created_obs.hazard_type, 'chemical')
        self.assertEqual(created_obs.priority, '3')
        self.assertEqual(created_obs.location_id.id, self.loc.id)
        self.assertEqual(created_obs.hazard_photo_filename, 'hazard_sample.jpg')
        self.assertTrue(bool(created_obs.hazard_photo))
