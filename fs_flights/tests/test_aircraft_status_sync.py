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
        aircraft = self._create_aircraft('TS-FLIGHT-02')
        flight = self._create_flight('FLT9002', aircraft)
        aircraft.write({'status': 'in_use'})

        with self.assertRaises(ValidationError):
            flight.action_start_flight()

    def test_flight_status_transitions_with_times(self):
        aircraft = self._create_aircraft('TS-FLIGHT-03')
        flight = self._create_flight('FLT9003', aircraft)

        # 1. Newly created flight should be scheduled
        self.assertEqual(flight.status, 'scheduled')

        # 2. Writing ATD (departure) only should move status to in_progress
        flight.write({'atd': 10.0})
        self.assertEqual(flight.status, 'in_progress')
        self.assertEqual(flight.atd, 10.0)
        self.assertEqual(flight.ata, 0.0)

        # 3. Writing ATA (arrival) should move status to done
        flight.write({'ata': 11.5})
        self.assertEqual(flight.status, 'done')
        self.assertEqual(flight.atd, 10.0)
        self.assertEqual(flight.ata, 11.5)

    def test_flight_status_onchange_transitions(self):
        aircraft = self._create_aircraft('TS-FLIGHT-04')
        flight = self._create_flight('FLT9004', aircraft)

        # Use new record for virtual record (onchange simulation)
        flight_form = self.env['fs.flight'].new({
            'callsign': 'FLT9004_V',
            'date': flight.date,
            'aircraft_id': aircraft.id,
        })
        # Simulate onchange
        flight_form.atd = 10.0
        flight_form._onchange_execution_times()
        self.assertEqual(flight_form.status, 'in_progress')

        # Now simulate setting both
        flight_form.ata = 11.5
        flight_form._onchange_execution_times()
        self.assertEqual(flight_form.status, 'done')
