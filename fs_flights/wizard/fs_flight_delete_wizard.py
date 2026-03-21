# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models, _
from odoo.exceptions import UserError


class FsFlightDeleteWizard(models.TransientModel):
    """Wizard to confirm the deletion of a flight with a warning."""

    _name = 'fs.flight.delete.wizard'
    _description = 'Confirm Flight Deletion'

    flight_log_id = fields.Many2one(
        comodel_name='fs.flight',
        string='Flight',
        required=True,
        readonly=True,
    )

    def action_delete(self):
        """Perform the deletion."""
        self.ensure_one()
        flight = self.flight_log_id
        if flight.status == 'done':
            raise UserError(_("You cannot delete a completed flight."))
        
        # Capture schedule ID before deletion
        schedule = flight.scheduled_flight_id

        # Delete the flight execution record
        flight.unlink()

        # Also delete the underlying scheduled flight if it exists (maintaining previous behavior)
        if schedule:
            schedule.unlink()
        
        return {'type': 'ir.actions.act_window_close'}
