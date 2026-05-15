# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Flights fs flight cancel wizard module.

Purpose:
    Defines classes FsFlightCancelWizard for daily operations boards, simulator operations, flight execution logs, cancellation workflows, schedule imports, and hour distribution.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_scheduling, fs_fleet, fs_training, fs_people, mail, bus.
    fs_scheduling provides planned flights.
"""
from odoo import api, fields, models, _


class FsFlightCancelWizard(models.TransientModel):
    """Wizard for cancelling flights with reason selection.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.flight.cancel.wizard``.
        _description (str): Human-readable model label, ``Cancel Flight Wizard``.

    Related:
        fs_scheduling provides planned flights.
        fs_training enrollments receive completed-hour updates.
    """

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
        """Confirm cancellation.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        self.flight_log_id.write({
            'status': 'cancelled',
            'cancellation_reason_id': self.cancellation_reason_id.id,
            'notes': self.notes,
            'atd': False,
            'ata': False,
        })

        return {'type': 'ir.actions.act_window_close'}
