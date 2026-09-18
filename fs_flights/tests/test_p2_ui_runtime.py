from odoo import fields
from odoo.tests.common import TransactionCase


class TestP2UiRuntime(TransactionCase):

    def test_carousel_interval_endpoint_preserves_zero_disable(self):
        parameter = self.env['ir.config_parameter'].sudo()
        parameter.set_param('flight_school.operations_carousel_interval', '0')

        self.assertEqual(
            self.env['fs.daily.operations'].get_carousel_interval(),
            0,
        )
        self.assertEqual(
            self.env['fs.simulator.operations'].get_carousel_interval(),
            0,
        )

        parameter.set_param('flight_school.operations_carousel_interval', 'not-a-number')
        self.assertEqual(
            self.env['fs.daily.operations'].get_carousel_interval(),
            10,
        )

    def test_board_actions_use_contextual_today(self):
        daily_action = self.env['fs.daily.operations'].action_open_operations_board()
        daily_board = self.env['fs.daily.operations'].browse(daily_action['res_id'])
        self.assertEqual(
            daily_board.date,
            fields.Date.context_today(self.env['fs.daily.operations']),
        )

        simulator_action = self.env['fs.simulator.operations'].action_open_simulator_board()
        simulator_board = self.env['fs.simulator.operations'].browse(
            simulator_action['res_id'],
        )
        self.assertEqual(
            simulator_board.date,
            fields.Date.context_today(self.env['fs.simulator.operations']),
        )
