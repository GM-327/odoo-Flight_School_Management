from datetime import datetime

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestP1Scheduling(TransactionCase):

    def test_timeline_datetime_normalization_uses_naive_utc(self):
        scheduled_flight_model = self.env['fs.scheduled.flight']

        start_datetime = scheduled_flight_model._normalize_timeline_datetime(
            '2026-09-18T10:00:00+02:00'
        )
        end_datetime = scheduled_flight_model._normalize_timeline_datetime(
            '2026-09-18T11:30:00+02:00'
        )

        self.assertEqual(start_datetime, datetime(2026, 9, 18, 8, 0))
        self.assertEqual(end_datetime, datetime(2026, 9, 18, 9, 30))
        self.assertEqual(
            (end_datetime - start_datetime).total_seconds(),
            90 * 60,
        )

    def test_action_schedule_rejects_missing_aircraft_before_creation(self):
        wizard = self.env['fs.scheduling.wizard'].create({})
        self.env['fs.scheduling.wizard.line'].create({
            'wizard_id': wizard.id,
            'callsign_number': 1,
        })
        scheduled_flight_model = self.env['fs.scheduled.flight']
        initial_count = scheduled_flight_model.search_count([])

        with self.assertRaises(UserError) as error:
            wizard.action_schedule()

        self.assertIn('assign an aircraft', str(error.exception))
        self.assertEqual(scheduled_flight_model.search_count([]), initial_count)
