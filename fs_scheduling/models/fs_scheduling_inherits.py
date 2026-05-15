# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Scheduling fs scheduling inherits module.

Purpose:
    Defines classes FsStudentEnrollment, FsInstructor, FsAircraft for planned flights, crew selection, route management, scheduling wizards, conflict detection, and timeline data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_training, fs_fleet, fs_people, mail, web_timeline.
    fs_flights publishes scheduled plans to operations boards.
"""
from odoo import api, fields, models


class FsStudentEnrollment(models.Model):
    """Odoo model for fs student enrollment.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.student.enrollment``.
        _inherit: Odoo model(s) extended by this class: ``['fs.student.enrollment']``.

    Related:
        fs_flights publishes scheduled plans to operations boards.
        fs_fleet supplies aircraft availability.
    """
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
        """Compute scheduled flights by searching for crew members matching this enrollment.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
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
        """Compute scheduled count values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.scheduled_count = len(record.scheduled_flight_ids)


class FsInstructor(models.Model):
    """Odoo model for fs instructor.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.instructor``.
        _inherit: Odoo model(s) extended by this class: ``['fs.instructor']``.

    Related:
        fs_flights publishes scheduled plans to operations boards.
        fs_fleet supplies aircraft availability.
    """
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
        """Compute scheduled flights by searching for crew members matching this instructor.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
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
        """Compute scheduled count values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.scheduled_count = len(record.scheduled_flight_ids)


class FsAircraft(models.Model):
    """Odoo model for fs aircraft.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.aircraft``.
        _inherit: Odoo model(s) extended by this class: ``['fs.aircraft']``.

    Related:
        fs_flights publishes scheduled plans to operations boards.
        fs_fleet supplies aircraft availability.
    """
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
        """Compute scheduled count values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.scheduled_count = len(record.scheduled_flight_ids)
