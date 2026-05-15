# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Flights fs import schedule wizard module.

Purpose:
    Defines classes FsImportScheduleWizard for daily operations boards, simulator operations, flight execution logs, cancellation workflows, schedule imports, and hour distribution.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_scheduling, fs_fleet, fs_training, fs_people, mail, bus.
    fs_scheduling provides planned flights.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FsImportScheduleWizard(models.TransientModel):
    """Wizard to import/publish scheduled flights to operations board.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.import.schedule.wizard``.
        _description (str): Human-readable model label, ``Import Schedule to Operations``.

    Related:
        fs_scheduling provides planned flights.
        fs_training enrollments receive completed-hour updates.
    """

    _name = 'fs.import.schedule.wizard'
    _description = 'Import Schedule to Operations'

    date = fields.Date(
        string='Date to Schedule',
        required=True,
        default=fields.Date.context_today,
    )
    scheduled_count = fields.Integer(
        string='Scheduled Flights',
        compute='_compute_counts',
    )
    already_published_count = fields.Integer(
        string='Already Published',
        compute='_compute_counts',
    )
    to_publish_count = fields.Integer(
        string='Flights to Publish',
        compute='_compute_counts',
    )

    @api.depends('date')
    def _compute_counts(self):
        """Compute statistics for the selected date.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        ScheduledFlight = self.env['fs.scheduled.flight']
        Flight = self.env['fs.flight']
        for record in self:
            if not record.date:
                record.scheduled_count = 0
                record.already_published_count = 0
                record.to_publish_count = 0
                continue

            # Count scheduled
            schedules = ScheduledFlight.search([
                ('date', '=', record.date),
            ])
            record.scheduled_count = len(schedules)

            # Count already published (linked)
            existing = Flight.search([
                ('scheduled_flight_id', 'in', schedules.ids)
            ])
            record.already_published_count = len(existing)

            # Remaining
            record.to_publish_count = record.scheduled_count - record.already_published_count

    def action_import(self):
        """Execute the import/publish action.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.

        Raises:
            UserError: If user-facing business validation fails.
        """
        self.ensure_one()
        if self.to_publish_count == 0:
            raise UserError(_("No new flights to publish for this date."))

        count = self.env['fs.scheduled.flight'].action_publish_day(self.date)  # type: ignore

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%s flights have been published to the Operations Board.') % count,
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
