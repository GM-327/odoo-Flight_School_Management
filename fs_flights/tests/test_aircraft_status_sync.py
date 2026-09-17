from datetime import date

from odoo.exceptions import UserError, ValidationError
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

    def test_midnight_times_are_recorded_and_distributed(self):
        aircraft = self._create_aircraft('TS-FLIGHT-05')
        flight = self._create_flight('FLT9005', aircraft)

        flight.write({'atd': 0.0})
        self.assertTrue(flight.atd_present)
        self.assertEqual(flight.status, 'in_progress')

        flight.write({'ata': 1.5})
        self.assertTrue(flight.ata_present)
        self.assertEqual(flight.status, 'done')
        self.assertEqual(flight.actual_duration, 1.5)
        self.assertEqual(flight.distributed_hours, 1.5)
        self.assertEqual(aircraft.total_hours, 1.5)

    def test_batch_times_reconcile_statuses_and_hours(self):
        first_aircraft = self._create_aircraft('TS-FLIGHT-06')
        second_aircraft = self._create_aircraft('TS-FLIGHT-07')
        flights = self._create_flight('FLT9006', first_aircraft) | self._create_flight(
            'FLT9007', second_aircraft,
        )

        flights.write({'atd': 0.0})
        self.assertEqual(set(flights.mapped('status')), {'in_progress'})
        self.assertEqual(set(flights.mapped('atd_present')), {True})
        self.assertEqual(first_aircraft.status, 'in_use')
        self.assertEqual(second_aircraft.status, 'in_use')

        flights.write({'ata': 1.0})
        self.assertEqual(set(flights.mapped('status')), {'done'})
        self.assertEqual(set(flights.mapped('distributed_hours')), {1.0})
        self.assertEqual(first_aircraft.total_hours, 1.0)
        self.assertEqual(second_aircraft.total_hours, 1.0)

    def test_batch_start_rejects_duplicate_active_aircraft(self):
        aircraft = self._create_aircraft('TS-FLIGHT-07A')
        flights = self._create_flight('FLT9007A', aircraft) | self._create_flight(
            'FLT9007B', aircraft,
        )

        with self.assertRaises(ValidationError):
            flights.write({'atd': 0.0})

        self.assertEqual(set(flights.mapped('status')), {'scheduled'})
        self.assertEqual(aircraft.status, 'available')

    def test_active_reassignment_requires_dispatchable_aircraft(self):
        first_aircraft = self._create_aircraft('TS-FLIGHT-08')
        second_aircraft = self._create_aircraft('TS-FLIGHT-09')
        first_flight = self._create_flight('FLT9008', first_aircraft)
        second_flight = self._create_flight('FLT9009', second_aircraft)

        first_flight.action_start_flight()
        second_flight.action_start_flight()

        with self.assertRaises(ValidationError):
            first_flight.write({'aircraft_id': second_aircraft.id})

    def test_active_reassignment_updates_both_aircraft_statuses(self):
        first_aircraft = self._create_aircraft('TS-FLIGHT-09A')
        second_aircraft = self._create_aircraft('TS-FLIGHT-09B')
        flight = self._create_flight('FLT9009A', first_aircraft)

        flight.action_start_flight()
        flight.write({'aircraft_id': second_aircraft.id})

        self.assertEqual(first_aircraft.status, 'available')
        self.assertEqual(second_aircraft.status, 'in_use')

    def test_active_flight_prevents_manual_availability_and_unlink_reconciles(self):
        aircraft = self._create_aircraft('TS-FLIGHT-10')
        flight = self._create_flight('FLT9010', aircraft)

        flight.action_start_flight()
        self.assertEqual(flight.status, 'in_progress')
        self.assertEqual(aircraft.status, 'in_use')
        with self.assertRaises(ValidationError):
            aircraft.action_set_available()

        flight.unlink()
        self.assertEqual(aircraft.status, 'available')

    def test_completed_flight_lifecycle_and_unlink_are_guarded(self):
        aircraft = self._create_aircraft('TS-FLIGHT-11')
        flight = self._create_flight('FLT9011', aircraft)

        with self.assertRaises(ValidationError):
            flight.write({'status': 'done'})

        flight.write({'atd': 9.0, 'ata': 10.0, 'status': 'done'})
        with self.assertRaises(UserError):
            flight.unlink()
        flight.write({'status': 'cancelled'})
        self.assertEqual(flight.status, 'cancelled')

    def test_publication_is_idempotent(self):
        aircraft = self._create_aircraft('TS-FLIGHT-12')
        route = self.env['fs.flight.route'].create({'name': 'Publication Test Route'})
        schedule = self.env['fs.scheduled.flight'].create({
            'callsign': 'FLT9012',
            'date': date.today(),
            'start_time': 8.0,
            'duration': 1.0,
            'flight_category': 'staff_training',
            'aircraft_id': aircraft.id,
            'route_id': route.id,
        })

        scheduled_flights = self.env['fs.scheduled.flight']
        self.assertEqual(scheduled_flights.action_publish_day(schedule.date), 1)
        self.assertEqual(scheduled_flights.action_publish_day(schedule.date), 0)
        self.assertEqual(
            self.env['fs.flight'].search_count([('scheduled_flight_id', '=', schedule.id)]),
            1,
        )
