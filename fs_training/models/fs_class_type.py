# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Training fs class type module.

Purpose:
    Defines classes FsClassType, FsClassTypeHours for class types, training classes, enrollments, missions, activities, completion tracking, and training KPIs.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
from odoo import api, fields, models


class FsClassType(models.Model):
    """Training class type templates.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.class.type``.
        _description (str): Human-readable model label, ``Class Type``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

    _name = 'fs.class.type'
    _description = 'Class Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Name',
        required=True,
        help='Class type name (e.g., PPL Course, Basic Training).',
    )
    code = fields.Char(
        string='Code',
        help='Short code.',
    )
    is_military = fields.Boolean(
        string='Military Only',
        default=False,
        help='This class type is for military students only.',
    )
    for_licensed_personnel = fields.Boolean(
        string='For Licensed Personnel',
        default=False,
        help=(
            'This class is for pilots/instructors (not students). '
            'Enables English and Qualification requirements.'
        ),
    )
    description = fields.Text(string='Description')
    reference_document = fields.Char(
        string='Reference Document',
        help='Document reference (for fs_documents module).',
    )
    duration_value = fields.Integer(
        string='Duration Value',
        help='Duration value to be used with the duration unit.',
    )
    duration_unit = fields.Selection(
        selection=[
            ('weeks', 'Weeks'),
            ('months', 'Months'),
        ],
        string='Duration Unit',
        default='weeks',
    )
    aircraft_type_ids = fields.Many2many(
        comodel_name='fs.aircraft.type',
        relation='fs_class_type_aircraft_type_rel',
        column1='class_type_id',
        column2='aircraft_type_id',
        string='Aircraft Types',
        help='Aircraft types used for this class.',
    )
    requirement_ids = fields.Many2many(
        comodel_name='fs.class.requirement',
        relation='fs_class_type_requirement_rel',
        column1='class_type_id',
        column2='requirement_id',
        string='Requirements',
        help='Enrollment requirements.',
    )
    hour_requirement_ids = fields.One2many(
        comodel_name='fs.class.type.hours',
        inverse_name='class_type_id',
        string='Hour Requirements',
        help='Minimum flight hours per discipline and type.',
    )
    flight_mission_ids = fields.One2many(
        comodel_name='fs.flight.mission',
        inverse_name='class_type_id',
        string='Flight Missions',
        help='Syllabus - flight missions for this class type.',
    )
    admin_task_ids = fields.One2many(
        comodel_name='fs.class.type.admin.task',
        inverse_name='class_type_id',
        string='Admin Tasks',
        help='Administrative tasks to create for each class (with custom order).',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help='Color index for badge display (0-11).',
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
        """Auto-add default requirements and admin tasks on create.

        Args:
            vals_list: List of value dictionaries passed to the multi-record create method.

        Returns:
            models.Model: Odoo recordset returned by the ORM.
        """
        default_requirements = self.env['fs.class.requirement'].search([
            ('is_default', '=', True),
        ])
        default_task_templates = self.env['fs.admin.task.template'].search([
            ('is_default', '=', True),
        ])

        for vals in vals_list:
            if default_requirements and not vals.get('requirement_ids'):
                vals['requirement_ids'] = [(6, 0, default_requirements.ids)]

            if default_task_templates and not vals.get('admin_task_ids'):
                vals['admin_task_ids'] = [
                    (0, 0, {'template_id': task.id, 'sequence': task.sequence})
                    for task in default_task_templates
                ]

        return super().create(vals_list)


class FsClassTypeHours(models.Model):
    """Minimum hour requirements per activity.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.class.type.hours``.
        _description (str): Human-readable model label, ``Class Type Hour Requirements``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

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
