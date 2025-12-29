# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from odoo.addons.fs_fleet.models.aircraft_type import AircraftType
    from .fs_class_requirement import FsClassRequirement
    from .fs_flight_mission import FsFlightMission
    from .fs_admin_task import FsAdminTaskTemplate


class FsClassType(models.Model):
    """Training class type templates."""

    _name = 'fs.class.type'
    _description = 'Class Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Name',
        required=True,
        help="Class type name (e.g., PPL Course, Basic Training).",
    )
    code = fields.Char(
        string='Code',
        help="Short code.",
    )
    is_military = fields.Boolean(
        string='Military Only',
        default=False,
        help="This class type is for military students only.",
    )
    for_licensed_personnel = fields.Boolean(
        string='For Licensed Personnel',
        default=False,
        help="This class is for pilots/instructors (not students). "
             "Enables English and Qualification requirements.",
    )
    description = fields.Text(
        string='Description',
    )
    reference_document = fields.Char(
        string='Reference Document',
        help="Document reference (for fs_documents module).",
    )
    duration_value = fields.Integer(
        string='Duration Value',
        help="Duration value to be used with the duration unit.",
    )
    duration_unit = fields.Selection(
        selection=[
            ('weeks', 'Weeks'),
            ('months', 'Months'),
        ],
        string='Duration Unit',
        default='weeks',
    )
    aircraft_type_ids: 'AircraftType' = fields.Many2many(  # type: ignore[assignment]
        comodel_name='fs.aircraft.type',
        relation='fs_class_type_aircraft_type_rel',
        column1='class_type_id',
        column2='aircraft_type_id',
        string='Aircraft Types',
        help="Aircraft types used for this class.",
    )
    requirement_ids: 'FsClassRequirement' = fields.Many2many(  # type: ignore[assignment]
        comodel_name='fs.class.requirement',
        relation='fs_class_type_requirement_rel',
        column1='class_type_id',
        column2='requirement_id',
        string='Requirements',
        help="Enrollment requirements.",
    )
    hour_requirement_ids: 'FsClassTypeHours' = fields.One2many(  # type: ignore[assignment]
        comodel_name='fs.class.type.hours',
        inverse_name='class_type_id',
        string='Hour Requirements',
        help="Minimum flight hours per discipline and type.",
    )
    flight_mission_ids: 'FsFlightMission' = fields.One2many(  # type: ignore[assignment]
        comodel_name='fs.flight.mission',
        inverse_name='class_type_id',
        string='Flight Missions',
        help="Syllabus - flight missions for this class type.",
    )
    admin_task_ids = fields.One2many(
        comodel_name='fs.class.type.admin.task',
        inverse_name='class_type_id',
        string='Admin Tasks',
        help="Administrative tasks to create for each class (with custom order).",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help="Color index for badge display (0-11).",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Class type code must be unique!',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-add default requirements and admin tasks on create if none provided."""
        default_reqs: 'FsClassRequirement' = self.env['fs.class.requirement'].search([('is_default', '=', True)])  # type: ignore
        default_tasks: 'FsAdminTaskTemplate' = self.env['fs.admin.task.template'].search([('is_default', '=', True)])  # type: ignore
        for vals in vals_list:
            # Auto-add default requirements if none provided
            if default_reqs and not vals.get('requirement_ids'):
                # Using command (6, 0, ids) is the standard Odoo way to set M2M relations in vals
                vals['requirement_ids'] = [(6, 0, default_reqs.ids)]
            # Auto-add default admin tasks if none provided
            if default_tasks and not vals.get('admin_task_ids'):
                # Using command (0, 0, vals) to create intermediate records linking to templates
                vals['admin_task_ids'] = [
                    (0, 0, {'template_id': task.id, 'sequence': task.sequence})
                    for task in default_tasks
                ]
        return super().create(vals_list)


class FsClassTypeHours(models.Model):
    """Minimum hour requirements per activity."""

    _name = 'fs.class.type.hours'
    _description = 'Class Type Hour Requirements'
    _order = 'activity_id'

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
    )
    discipline_id = fields.Many2one(
        comodel_name='fs.flight.discipline',
        related='activity_id.discipline_id',
        store=True,
    )
    flight_type_id = fields.Many2one(
        comodel_name='fs.flight.type',
        related='activity_id.flight_type_id',
        store=True,
    )
    minimum_hours = fields.Float(
        string='Minimum Hours',
        required=True,
        default=0.0,
    )

    _unique_activity = models.Constraint(
        'UNIQUE(class_type_id, activity_id)',
        'This activity is already defined for this class type!',
    )
