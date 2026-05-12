# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsStudentEnrollment(models.Model):
    _name = 'fs.student.enrollment'
    _inherit = ['fs.student.enrollment']

    scheduled_flight_ids = fields.Many2many(
        comodel_name='fs.scheduled.flight',
        string='Scheduled Flights',
        compute='_compute_scheduled_flights',
    )
    scheduled_count = fields.Integer(
        string='Scheduled Count',
        compute='_compute_scheduled_count',
    )

    def _compute_scheduled_flights(self):
        """Compute scheduled flights by searching for crew members matching this enrollment."""
        for record in self:
            # Student crew rows keep source_id as the student id and expose enrollment_id separately.
            crew_member = self.env['fs.crew.member'].search([
                ('enrollment_id', '=', record.id),
            ], limit=1)
            if crew_member:
                record.scheduled_flight_ids = self.env['fs.scheduled.flight'].search([
                    '|',
                    ('pilot1_crew_id', '=', crew_member.id),
                    ('pilot2_crew_id', '=', crew_member.id),
                ])
            else:
                record.scheduled_flight_ids = False

    @api.depends('scheduled_flight_ids')
    def _compute_scheduled_count(self):
        for record in self:
            record.scheduled_count = len(record.scheduled_flight_ids)


class FsInstructor(models.Model):
    _name = 'fs.instructor'
    _inherit = ['fs.instructor']

    scheduled_flight_ids = fields.Many2many(
        comodel_name='fs.scheduled.flight',
        string='Scheduled Flights',
        compute='_compute_scheduled_flights',
    )
    scheduled_count = fields.Integer(
        compute='_compute_scheduled_count',
    )

    def _compute_scheduled_flights(self):
        """Compute scheduled flights by searching for crew members matching this instructor."""
        for record in self:
            # Find the crew member ID for this instructor (offset + 1000000)
            crew_member = self.env['fs.crew.member'].search([
                ('source_model', '=', 'fs.instructor'),
                ('source_id', '=', record.id)
            ], limit=1)
            if crew_member:
                record.scheduled_flight_ids = self.env['fs.scheduled.flight'].search([
                    '|',
                    ('pilot1_crew_id', '=', crew_member.id),
                    ('pilot2_crew_id', '=', crew_member.id),
                ])
            else:
                record.scheduled_flight_ids = False

    def _compute_scheduled_count(self):
        for record in self:
            record.scheduled_count = len(record.scheduled_flight_ids)


class FsAircraft(models.Model):
    _name = 'fs.aircraft'
    _inherit = ['fs.aircraft']

    scheduled_flight_ids = fields.One2many(
        comodel_name='fs.scheduled.flight',
        inverse_name='aircraft_id',
        string='Scheduled Flights',
    )
    scheduled_count = fields.Integer(
        compute='_compute_scheduled_count',
    )

    def _compute_scheduled_count(self):
        for record in self:
            record.scheduled_count = len(record.scheduled_flight_ids)
