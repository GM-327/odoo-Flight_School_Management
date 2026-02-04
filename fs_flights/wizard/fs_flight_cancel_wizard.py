# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _


class FsFlightCancelWizard(models.TransientModel):
    """Wizard for cancelling flights with reason selection."""

    _name = 'fs.flight.cancel.wizard'
    _description = 'Cancel Flight Wizard'

    flight_log_id = fields.Many2one(
        comodel_name='fs.flight',
        string='Flight',
        required=True,
    )
    callsign = fields.Char(
        related='flight_log_id.callsign',
        readonly=True,
    )
    cancellation_reason_id = fields.Many2one(
        comodel_name='fs.cancellation.reason',
        string='Reason',
        required=True,
    )
    notes = fields.Text(string='Notes')

    def action_confirm(self):
        """Confirm cancellation."""
        self.ensure_one()
        self.flight_log_id.write({
            'status': 'cancelled',
            'cancellation_reason_id': self.cancellation_reason_id.id,
            'notes': self.notes,
            'atd': False,
            'ata': False,
        })

        return {'type': 'ir.actions.act_window_close'}
