# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Training fs flight mission module.

Purpose:
    Defines classes FsFlightMission for class types, training classes, enrollments, missions, activities, completion tracking, and training KPIs.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
import re
from odoo import api, fields, models


class FsFlightMission(models.Model):
    """Syllabus flight missions for class types.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.flight.mission``.
        _description (str): Human-readable model label, ``Flight Mission``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

    _name = 'fs.flight.mission'
    _description = 'Flight Mission'
    _order = 'class_type_id, sequence, id'

    name = fields.Char(
        string='Mission Name',
        required=True,
    )
    class_type_id = fields.Many2one(
        comodel_name='fs.class.type',
        string='Class Type',
        required=True,
        ondelete='cascade',
    )
    activity_id = fields.Many2one(
        comodel_name='fs.flight.activity',
        string='Activity',
        required=True,
        ondelete='restrict',
        help="Flight activity (combination of discipline and type).",
    )
    discipline_id = fields.Many2one(
        comodel_name='fs.flight.discipline',
        related='activity_id.discipline_id',
        store=True,
    )
    discipline_color = fields.Integer(
        string='Discipline Color',
        related='discipline_id.color',
    )
    flight_type_id = fields.Many2one(
        comodel_name='fs.flight.type',
        related='activity_id.flight_type_id',
        store=True,
    )
    flight_type_color = fields.Integer(
        string='Flight Type Color',
        related='flight_type_id.color',
    )
    is_exam = fields.Boolean(
        string='Is Exam',
        default=False,
        help="Check if this mission is an evaluation or final exam.",
    )
    is_sim = fields.Boolean(
        string='Is Simulator',
        related='activity_id.is_sim',
        store=True,
        help="Indicates if this mission is a simulator session.",
    )
    is_extra = fields.Boolean(
        string='Is Extra/Revision',
        default=False,
        help="If checked, this mission is for revision or extra practice and doesn't count as a mandatory syllabus step.",
    )
    duration_hours = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration_hours',
        store=True,
        readonly=False,
        help="Expected duration. Defaults from discipline.",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    description = fields.Text(
        string='Description',
        related='discipline_id.description',
        readonly=True,
    )
    objectives = fields.Text(
        string='Objectives',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    @api.depends('activity_id', 'discipline_id')
    def _compute_duration_hours(self):
        """Default duration from discipline.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            if record.discipline_id and not record.duration_hours:
                record.duration_hours = record.discipline_id.default_flight_duration  # type: ignore
            elif not record.duration_hours:
                record.duration_hours = 1.0

    @api.onchange('activity_id')
    def _onchange_activity_id(self):
        """Update duration from discipline when activity is changed.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.activity_id and self.activity_id.discipline_id:  # type: ignore
            self.duration_hours = self.activity_id.discipline_id.default_flight_duration  # type: ignore

    def action_duplicate_mission(self):
        """Duplicate mission with incremented name and sequence.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        current_name = self.name or ""
        match = re.search(r'(\d+)$', current_name)
        if match:
            number = int(match.group(1))
            prefix = current_name[:match.start()]
            new_name = f"{prefix}{number + 1}"
        else:
            new_name = f"{current_name} 2"

        # Copy the mission with new name and slightly higher sequence
        # to ensure it appears right after the current one.
        new_record = self.copy(default={
            'name': new_name,
            'sequence': self.sequence + 1,
        })
        # Return False to avoid full page reload - view will auto-refresh
        return False
