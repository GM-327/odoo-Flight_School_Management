from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestFlightAircraftStatusSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['fs.aircraft.category'].create({
            'name': 'Flight Test Category',
            'code': 'ftc',
        })
        cls.aircraft_type = cls.env['fs.aircraft.type'].create({
            'name': 'Flight Test Model',
            'manufacturer': 'Flight Test Manufacturer',
            'category_id': cls.category.id,
        })

    def _create_aircraft(self, registration, **extra_vals):
        vals = {
            'registration': registration,
            'aircraft_type_id': self.aircraft_type.id,
        }
        vals.update(extra_vals)
        return self.env['fs.aircraft'].create(vals)

    def _create_flight(self, callsign, aircraft, **extra_vals):
        vals = {
            'callsign': callsign,
            'date': date.today(),
            'scheduled_start': 8.0,
            'scheduled_duration': 1.0,
            'flight_category': 'staff_training',
            'aircraft_id': aircraft.id,
        }
        vals.update(extra_vals)
        return self.env['fs.flight'].create(vals)

    def test_start_and_complete_sync_aircraft_status(self):
        aircraft = self._create_aircraft('TS-FLIGHT-01')
        flight = self._create_flight('FLT9001', aircraft)

        flight.action_start_flight()
        self.assertEqual(aircraft.status, 'in_use')

        flight.action_complete_flight()
        self.assertEqual(aircraft.status, 'available')

    def test_start_blocks_when_aircraft_not_available(self):
        aircraft = self._create_aircraft('TS-FLIGHT-02', status='in_use')
        flight = self._create_flight('FLT9002', aircraft)

        with self.assertRaises(ValidationError):
            flight.action_start_flight()
