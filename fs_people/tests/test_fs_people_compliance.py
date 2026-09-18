from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestFsPeopleCompliance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.today = fields.Date.today()
        self.parameters = self.env['ir.config_parameter'].sudo()
        for setting_name, warning_days in (
            ('medical_warning_days', 35),
            ('license_warning_days', 35),
            ('english_warning_days', 60),
            ('security_warning_days', 60),
            ('insurance_warning_days', 14),
        ):
            self.parameters.set_param(f'flight_school.{setting_name}', warning_days)

    def test_daily_refresh_updates_boundary_statuses_and_eligibility(self):
        instructor = self.env['fs.instructor'].create({
            'name': 'Compliance Boundary Instructor',
            'gender': 'female',
            'medical_expiry': self.today,
            'english_expiry': self.today,
        })
        qualification_type = self.env['fs.qualification.type'].create({
            'name': 'Boundary Qualification',
            'code': 'BOUNDARY',
        })
        qualification = self.env['fs.person.qualification'].create({
            'instructor_id': instructor.id,
            'qualification_id': qualification_type.id,
            'expiry_date': self.today,
        })
        student = self.env['fs.student'].create({
            'name': 'Compliance Boundary Student',
            'gender': 'male',
            'license_expiry': self.today,
        })
        pilot = self.env['fs.pilot'].create({
            'name': 'Compliance Boundary Pilot',
            'gender': 'male',
            'security_clearance_expiry': self.today,
            'insurance_expiry': self.today,
        })

        tomorrow = self.today + timedelta(days=1)
        with patch.object(fields.Date, 'context_today', return_value=tomorrow):
            self.env['fs.person'].cron_refresh_compliance_statuses()

        self.assertEqual(instructor.medical_status, 'expired')
        self.assertEqual(instructor.english_status, 'expired')
        self.assertEqual(qualification.expiry_status, 'expired')
        self.assertEqual(instructor.eligibility_status, 'not_eligible')
        self.assertTrue(instructor.has_expired_qualification)
        self.assertEqual(student.license_expiry_status, 'expired')
        self.assertTrue(student.has_expired_status)
        self.assertEqual(pilot.security_clearance_status, 'expired')
        self.assertEqual(pilot.insurance_status, 'expired')

    def test_warning_setting_change_refreshes_stored_statuses(self):
        pilot = self.env['fs.pilot'].create({
            'name': 'Compliance Settings Pilot',
            'gender': 'male',
            'english_expiry': self.today + timedelta(days=10),
        })
        self.assertEqual(pilot.english_status, 'expiring')

        settings = self.env['res.config.settings'].create({
            'fs_english_warning_days': 5,
        })
        settings.set_values()

        self.assertEqual(self.parameters.get_param('flight_school.english_warning_days'), '5')
        self.assertEqual(pilot.english_status, 'valid')

    def test_invalid_runtime_warning_values_use_settings_defaults(self):
        warning_defaults = {
            'medical_warning_days': 35,
            'license_warning_days': 35,
            'english_warning_days': 60,
            'security_warning_days': 60,
            'insurance_warning_days': 14,
        }
        for setting_name, warning_days in warning_defaults.items():
            self.parameters.set_param(f'flight_school.{setting_name}', 'invalid')
            self.assertEqual(
                self.env['fs.person']._get_compliance_warning_days(setting_name),
                warning_days,
            )

    def test_people_dashboard_includes_expiring_qualifications(self):
        instructor = self.env['fs.instructor'].create({
            'name': 'Dashboard Expiring Qualification Instructor',
            'gender': 'female',
        })
        qualification_type = self.env['fs.qualification.type'].create({
            'name': 'Dashboard Expiring Qualification',
            'code': 'DASH-EXP',
        })
        self.env['fs.person.qualification'].create({
            'instructor_id': instructor.id,
            'qualification_id': qualification_type.id,
            'expiry_date': self.today + timedelta(days=1),
        })

        dashboard = self.env['fs.people.dashboard'].new({})
        dashboard._compute_instructor_kpis()

        self.assertEqual(dashboard.instructor_expiring, 1)
        self.assertIn(
            ('qualification_ids.expiry_status', '=', 'expiring'),
            dashboard.action_view_instructors_expiring()['domain'],
        )
