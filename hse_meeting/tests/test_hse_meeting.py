# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import datetime

class TestHSEMeeting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Dept = cls.env['hse.meeting.department']
        cls.MeetingType = cls.env['hse.meeting.type']
        cls.Meeting = cls.env['hse.meeting']

        cls.dept = cls.Dept.create({
            'name': 'Offshore Production Operations',
            'number_of_employees': 40,
        })
        cls.meeting_type = cls.MeetingType.create({
            'name': 'Daily Pre-Shift Toolbox Talk',
        })

    def test_01_department_creation_and_validation(self):
        dept = self.Dept.create({
            'name': 'Process Safety Engineering',
            'number_of_employees': 25,
        })
        self.assertEqual(dept.number_of_employees, 25)

        with self.assertRaises(ValidationError):
            self.Dept.create({
                'name': 'Invalid Dept',
                'number_of_employees': -5,
            })

    def test_02_meeting_creation_and_computation(self):
        meeting = self.Meeting.create({
            'meeting_datetime': datetime.now(),
            'duration': 1.5,
            'department_id': self.dept.id,
            'meeting_type_ids': self.meeting_type.id,
            'topic': 'Permit to Work and Hot Work Safeguards',
            'present_employees': 30,
            'meeting_attend_employees': 24,
        })
        # Check computed fields
        self.assertEqual(meeting.total_employees, 40)
        # (24 meeting attendees / 30 present employees) * 100 = 80%
        self.assertEqual(meeting.percentage_total_attendees, 80)

    def test_03_employee_counts_validation_rules(self):
        # 1. Negative attendee numbers
        with self.assertRaises(ValidationError):
            self.Meeting.create({
                'department_id': self.dept.id,
                'present_employees': -10,
                'meeting_attend_employees': 5,
            })

        # 2. Meeting attendees exceed present employees
        with self.assertRaises(ValidationError):
            self.Meeting.create({
                'department_id': self.dept.id,
                'present_employees': 20,
                'meeting_attend_employees': 25,
            })

        # 3. Present employees exceed total department employees (40)
        with self.assertRaises(ValidationError):
            self.Meeting.create({
                'department_id': self.dept.id,
                'present_employees': 45,
                'meeting_attend_employees': 20,
            })

    def test_04_open_corrective_action_form(self):
        meeting = self.Meeting.create({
            'department_id': self.dept.id,
            'meeting_type_ids': self.meeting_type.id,
            'topic': 'Housekeeping & Chemical Storage Issues',
            'present_employees': 20,
            'meeting_attend_employees': 20,
        })
        action = meeting.open_corrective_form()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'hse.capa.model')
        self.assertEqual(action.get('context', {}).get('default_select_department'), self.dept.id)
