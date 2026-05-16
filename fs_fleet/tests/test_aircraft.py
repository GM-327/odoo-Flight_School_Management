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

    def test_operational_warning_lists_missing_and_expired_documents(self):
        aircraft = self._create_aircraft(
            'TS-TEST-06',
            insurance_expiry=date.today() - timedelta(days=1),
        )
        self.assertTrue(aircraft.has_operational_warning)
        self.assertIn('Insurance has expired.', aircraft.operational_warning)
        self.assertIn('Certificate of Airworthiness expiry date is missing.', aircraft.operational_warning)
        self.assertIn('ARC expiry date is missing.', aircraft.operational_warning)
