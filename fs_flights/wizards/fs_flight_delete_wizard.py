# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Flights fs flight delete wizard module.

Purpose:
    Defines classes FsFlightDeleteWizard for daily operations boards, simulator operations, flight execution logs, cancellation workflows, schedule imports, and hour distribution.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_scheduling, fs_fleet, fs_training, fs_people, mail, bus.
    fs_scheduling provides planned flights.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FsFlightDeleteWizard(models.TransientModel):
    """Wizard to confirm the deletion of a flight with a warning.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.flight.delete.wizard``.
        _description (str): Human-readable model label, ``Confirm Flight Deletion``.

    Related:
        fs_scheduling provides planned flights.
        fs_training enrollments receive completed-hour updates.
    """

    _name = 'fs.flight.delete.wizard'
    _description = 'Confirm Flight Deletion'

    flight_log_id = fields.Many2one(
        comodel_name='fs.flight',
        string='Flight',
        required=True,
        readonly=True,
    )

    def action_delete(self):
        """Perform the deletion.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.

        Raises:
            UserError: If user-facing business validation fails.
        """
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
