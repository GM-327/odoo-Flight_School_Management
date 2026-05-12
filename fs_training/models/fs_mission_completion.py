# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsMissionCompletion(models.Model):
    """Track mission completion status per enrollment.

    This model records which missions have been completed by students
    within their enrollment, along with completion dates and notes.
    """
    _name = 'fs.mission.completion'
    _description = 'Mission Completion'
    _order = 'completion_date desc, id desc'
    _rec_name = 'display_name'

    enrollment_id = fields.Many2one(
        'fs.student.enrollment',
        string='Enrollment',
        required=True,
        ondelete='cascade',
        index=True,
    )
    student_id = fields.Many2one(
        comodel_name='fs.student',
        related='enrollment_id.student_id',
        store=True,
        string='Student',
    )
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        related='enrollment_id.training_class_id',
        store=True,
        string='Training Class',
    )
    mission_id = fields.Many2one(
        'fs.flight.mission',
        string='Mission',
        required=True,
        ondelete='restrict',
        index=True,
    )
    mission_name = fields.Char(
        related='mission_id.name',
        string='Mission Name',
    )

    is_completed = fields.Boolean(
        string='Completed',
        default=False,
    )
    completion_date = fields.Date(
        string='Completion Date',
    )
    # Note: flight_id is defined in fs_flights module via inheritance
    # to avoid circular dependency between fs_training and fs_flights
    notes = fields.Text(
        string='Notes',
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    _unique_enrollment_mission = models.Constraint(
        'UNIQUE(enrollment_id, mission_id)',
        'A mission can only be tracked once per enrollment.',
    )

    @api.depends('enrollment_id.student_id.display_name', 'mission_id.name')
    def _compute_display_name(self):
        for record in self:
            student_name = record.student_id.display_name or 'Unknown'
            mission_name = record.mission_name or 'N/A'
            record.display_name = f"{student_name} - {mission_name}"

    @api.onchange('is_completed')
    def _onchange_is_completed(self):
        if self.is_completed and not self.completion_date:
            self.completion_date = fields.Date.context_today(self)
        elif not self.is_completed:
            self.completion_date = False

    def action_mark_complete(self):
        """Mark the mission as completed."""
        for record in self:
            record.write({
                'is_completed': True,
                'completion_date': fields.Date.context_today(self),
            })

    def action_mark_incomplete(self):
        """Mark the mission as not completed."""
        for record in self:
            record.write({
                'is_completed': False,
                'completion_date': False,
            })
