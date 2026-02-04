# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class FsImportScheduleWizard(models.TransientModel):
    """Wizard to import/publish scheduled flights to operations board."""

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
        """Compute statistics for the selected date."""
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
        """Execute the import/publish action."""
        self.ensure_one()
        if self.to_publish_count == 0:
            raise UserError(_("No new flights to publish for this date."))
            
        count = self.env['fs.scheduled.flight'].action_publish_day(self.date) # type: ignore
        
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
