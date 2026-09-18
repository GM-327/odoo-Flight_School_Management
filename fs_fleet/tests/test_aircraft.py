from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestFleetAircraft(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['fs.aircraft.category'].create({
            'name': 'Test Category',
            'code': 'tca',
        })
        cls.aircraft_type = cls.env['fs.aircraft.type'].create({
            'name': 'Test Model',
            'manufacturer': 'Test Manufacturer',
            'category_id': cls.category.id,
        })

    def _create_aircraft(self, registration, **extra_vals):
        vals = {
            'registration': registration,
            'aircraft_type_id': self.aircraft_type.id,
        }
        vals.update(extra_vals)
        return self.env['fs.aircraft'].create(vals)

    def test_registration_is_normalized_on_create(self):
        aircraft = self._create_aircraft(' ts-test-01 ')
        self.assertEqual(aircraft.registration, 'TS-TEST-01')

    def test_category_code_is_normalized_on_create(self):
        self.assertEqual(self.category.code, 'TCA')

    def test_missing_maintenance_thresholds_are_not_configured(self):
        aircraft = self._create_aircraft('TS-TEST-02')
        self.env['fs.aircraft'].cron_refresh_aircraft_maintenance_status()
        self.assertEqual(aircraft.maintenance_hour_status, 'not_configured')
        self.assertEqual(aircraft.maintenance_date_status, 'not_configured')
        self.assertEqual(aircraft.maintenance_status, 'not_configured')

    def test_airworthiness_and_assignment_follow_status(self):
        aircraft = self._create_aircraft('TS-TEST-03')
        self.assertTrue(aircraft.is_airworthy)
        self.assertTrue(aircraft.is_available_for_assignment)

        aircraft.write({'status': 'in_use'})
        self.assertTrue(aircraft.is_airworthy)
        self.assertFalse(aircraft.is_available_for_assignment)

        aircraft.write({'status': 'maintenance'})
        self.assertFalse(aircraft.is_airworthy)
        self.assertEqual(aircraft.airworthiness_blocker, 'maintenance')

        aircraft.write({'status': 'grounded'})
        self.assertFalse(aircraft.is_airworthy)
        self.assertEqual(aircraft.airworthiness_blocker, 'grounded')

    def test_overdue_maintenance_remains_schedulable_warning(self):
        aircraft = self._create_aircraft(
            'TS-TEST-04',
            total_hours=120.0,
            maintenance_due_at_hours=100.0,
        )
        self.env['fs.aircraft'].cron_refresh_aircraft_maintenance_status()
        self.assertEqual(aircraft.maintenance_status, 'overdue')
        aircraft._check_schedulable_aircraft(expected_simulator=False)

    def test_dispatch_requires_current_availability(self):
        aircraft = self._create_aircraft('TS-TEST-05', status='in_use')
        with self.assertRaises(ValidationError):
            aircraft._check_dispatchable_aircraft(expected_simulator=False)

    def test_archived_aircraft_cannot_be_scheduled_or_dispatched(self):
        aircraft = self._create_aircraft('TS-TEST-05A', active=False)
        self.assertFalse(aircraft.is_available_for_assignment)
        with self.assertRaises(ValidationError):
            aircraft._check_schedulable_aircraft(expected_simulator=False)
        with self.assertRaises(ValidationError):
            aircraft._check_dispatchable_aircraft(expected_simulator=False)

    def test_manager_cannot_access_global_settings(self):
        manager_group = self.env.ref('fs_core.group_flight_school_manager')
        manager_user = self.env['res.users'].create({
            'name': 'Fleet Settings Manager',
            'login': 'fleet.settings.manager@example.com',
            'group_ids': [(6, 0, [manager_group.id])],
        })

        self.assertFalse(
            self.env['res.config.settings'].with_user(manager_user).has_access('create')
        )

    def test_operational_warning_lists_missing_and_expired_documents(self):
        aircraft = self._create_aircraft(
            'TS-TEST-06',
            insurance_expiry=date.today() - timedelta(days=1),
        )
        self.assertTrue(aircraft.has_operational_warning)
        self.assertIn('Insurance has expired.', aircraft.operational_warning)
        self.assertIn('Certificate of Airworthiness expiry date is missing.', aircraft.operational_warning)
        self.assertIn('ARC expiry date is missing.', aircraft.operational_warning)

    def test_fleet_dashboard_counts_missing_certificates(self):
        aircraft = self._create_aircraft('TS-TEST-07')
        dashboard = self.env['fs.fleet.dashboard'].new({})
        dashboard._compute_certificate_kpis()

        self.assertIn(
            aircraft,
            self.env['fs.aircraft'].search(
                dashboard.action_view_cert_expired()['domain'],
            ),
        )
        self.assertGreaterEqual(dashboard.cert_expired, 1)

    def test_empty_fleet_reports_zero_availability(self):
        aircraft_model = self.env['fs.aircraft']
        aircraft_model.with_context(active_test=False).search([]).write({'active': False})
        dashboard = self.env['fs.fleet.dashboard'].new({})
        dashboard._compute_summary_kpis()

        self.assertEqual(dashboard.fleet_total, 0)
        self.assertEqual(dashboard.fleet_availability, 0.0)
