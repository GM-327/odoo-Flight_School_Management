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
from odoo.exceptions import ValidationError


REQUIREMENT_GROUP_COUNT_AS_SELECTION = [
    ('aircraft', 'Aircraft'),
    ('simulator', 'Simulator'),
    ('unallocated', 'Unallocated'),
]


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
    hour_requirement_group_ids = fields.One2many(
        comodel_name='fs.class.type.hours.group',
        inverse_name='class_type_id',
        string='Alternative Hour Requirement Groups',
        help='OR hour requirements that can be satisfied by any listed activity.',
    )
    total_required_hours = fields.Float(
        string='Total Required Hours',
        compute='_compute_required_hour_totals',
        store=True,
        help='Total minimum training hours required for this class type.',
    )
    total_required_aircraft_hours = fields.Float(
        string='Total Req. A/C Hours',
        compute='_compute_required_hour_totals',
        store=True,
        help='Total minimum aircraft hours required for this class type.',
    )
    total_required_simulator_hours = fields.Float(
        string='Total Req. SIM Hours',
        compute='_compute_required_hour_totals',
        store=True,
        help='Total minimum simulator hours required for this class type.',
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

    @api.depends(
        'hour_requirement_ids.minimum_hours',
        'hour_requirement_ids.activity_id.is_sim',
        'hour_requirement_ids.requirement_group_id',
        'hour_requirement_group_ids.minimum_hours',
        'hour_requirement_group_ids.count_as',
    )
    def _compute_required_hour_totals(self):
        """Compute required training hour totals split by aircraft and simulator."""
        for record in self:
            total_required_hours = 0.0
            total_required_aircraft_hours = 0.0
            total_required_simulator_hours = 0.0

            standalone_requirements = record.hour_requirement_ids.filtered(
                lambda requirement: not requirement.requirement_group_id
            )
            for hour_requirement in standalone_requirements:
                minimum_hours = hour_requirement.minimum_hours
                total_required_hours += minimum_hours
                if hour_requirement.activity_id.is_sim:
                    total_required_simulator_hours += minimum_hours
                else:
                    total_required_aircraft_hours += minimum_hours

            for requirement_group in record.hour_requirement_group_ids:
                minimum_hours = requirement_group.minimum_hours
                total_required_hours += minimum_hours
                if requirement_group.count_as == 'aircraft':
                    total_required_aircraft_hours += minimum_hours
                elif requirement_group.count_as == 'simulator':
                    total_required_simulator_hours += minimum_hours

            record.total_required_hours = total_required_hours
            record.total_required_aircraft_hours = total_required_aircraft_hours
            record.total_required_simulator_hours = total_required_simulator_hours

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


class FsClassTypeHoursGroup(models.Model):
    """Alternative hour requirement group for a class type.

    A group represents one OR requirement bucket. Any combination of the
    group's activities can satisfy the group's minimum hours.
    """

    _name = 'fs.class.type.hours.group'
    _description = 'Class Type Alternative Hour Requirement Group'
    _order = 'class_type_id, sequence, name'

    class_type_id = fields.Many2one(
        comodel_name='fs.class.type',
        string='Class Type',
        required=True,
        ondelete='cascade',
    )
    name = fields.Char(
        string='Name',
        required=True,
        help='Label shown for this alternative hour requirement.',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    operator = fields.Selection(
        selection=[('any', 'Any')],
        string='Operator',
        default='any',
        required=True,
        readonly=True,
        help='Any listed activity can contribute to this requirement.',
    )
    minimum_hours = fields.Float(
        string='Required Hours',
        required=True,
        default=0.0,
        help='Hours required across any combination of alternative activities.',
    )
    count_as = fields.Selection(
        selection=REQUIREMENT_GROUP_COUNT_AS_SELECTION,
        string='Count As',
        required=True,
        default='unallocated',
        help='Determines whether this group contributes to aircraft or simulator totals.',
    )
    hour_requirement_ids = fields.One2many(
        comodel_name='fs.class.type.hours',
        inverse_name='requirement_group_id',
        string='Alternative Activities',
        help='Activities that can satisfy this OR requirement.',
    )
    alternative_activity_names = fields.Char(
        string='Alternative Activity Names',
        compute='_compute_alternative_activity_names',
    )

    @api.depends('hour_requirement_ids.activity_id.name')
    def _compute_alternative_activity_names(self):
        """Display alternative activity names in list views."""
        for record in self:
            record.alternative_activity_names = ' / '.join(
                record.hour_requirement_ids.mapped('activity_id.display_name')
            )

    @api.constrains('minimum_hours')
    def _check_minimum_hours(self):
        """Require a positive OR-group minimum."""
        for record in self:
            if record.minimum_hours <= 0.0:
                raise ValidationError('Alternative requirement groups must require positive hours.')

    @api.constrains('hour_requirement_ids')
    def _check_alternative_count(self):
        """Require at least two alternatives in every OR group."""
        for record in self:
            if len(record.hour_requirement_ids) < 2:
                raise ValidationError(
                    'Alternative requirement groups must contain at least two activities.'
                )

    @api.constrains('class_type_id', 'hour_requirement_ids')
    def _check_alternative_class_type(self):
        """Ensure alternatives remain attached to the same class type as the group."""
        for record in self:
            mismatched_lines = record.hour_requirement_ids.filtered(
                lambda line: line.class_type_id != record.class_type_id
            )
            if mismatched_lines:
                raise ValidationError(
                    'Alternative activities must belong to the same class type as their group.'
                )


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
    requirement_group_id = fields.Many2one(
        comodel_name='fs.class.type.hours.group',
        string='OR Group',
        ondelete='cascade',
        help='If set, this activity is an alternative for the selected OR group.',
    )
    requirement_group_name = fields.Char(
        string='OR Group Name',
        related='requirement_group_id.name',
        store=True,
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

    @api.model_create_multi
    def create(self, vals_list):
        """Default the class type from the OR group when creating alternatives."""
        group_ids = {
            vals.get('requirement_group_id')
            for vals in vals_list
            if vals.get('requirement_group_id') and not vals.get('class_type_id')
        }
        groups_by_id = {
            group.id: group
            for group in self.env['fs.class.type.hours.group'].browse(group_ids)
        }
        for vals in vals_list:
            group_id = vals.get('requirement_group_id')
            if group_id and not vals.get('class_type_id'):
                vals['class_type_id'] = groups_by_id[group_id].class_type_id.id
            if group_id and 'minimum_hours' not in vals:
                vals['minimum_hours'] = 0.0
        return super().create(vals_list)

    def write(self, vals):
        """Keep class type aligned when an activity is moved into an OR group."""
        if vals.get('requirement_group_id') and not vals.get('class_type_id'):
            vals = dict(vals)
            group = self.env['fs.class.type.hours.group'].browse(vals['requirement_group_id'])
            vals['class_type_id'] = group.class_type_id.id
        return super().write(vals)

    @api.onchange('requirement_group_id')
    def _onchange_requirement_group_id(self):
        """Default class type and clear standalone minimums for alternatives."""
        for record in self:
            if record.requirement_group_id:
                record.class_type_id = record.requirement_group_id.class_type_id
                record.minimum_hours = 0.0

    @api.constrains('class_type_id', 'requirement_group_id')
    def _check_group_class_type(self):
        """Ensure grouped alternatives use their group's class type."""
        for record in self:
            if (
                record.requirement_group_id
                and record.class_type_id != record.requirement_group_id.class_type_id
            ):
                raise ValidationError(
                    'Grouped hour requirements must use the same class type as their OR group.'
                )

    @api.constrains('class_type_id', 'activity_id', 'requirement_group_id')
    def _check_duplicate_activity_scope(self):
        """Prevent duplicate standalone or duplicate in-group activities.

        The same activity can appear in multiple OR groups for the same class
        type, but not twice in one group and not twice as a standalone line.
        """
        records = self.filtered(lambda record: record.class_type_id and record.activity_id)
        if not records:
            return

        candidate_lines = self.search([
            ('class_type_id', 'in', records.mapped('class_type_id').ids),
            ('activity_id', 'in', records.mapped('activity_id').ids),
        ])
        seen_keys = set()
        for line in candidate_lines:
            if line.requirement_group_id:
                scope_key = ('group', line.requirement_group_id.id, line.activity_id.id)
            else:
                scope_key = ('standalone', line.class_type_id.id, line.activity_id.id)
            if scope_key in seen_keys:
                raise ValidationError(
                    'This activity is already defined in the same requirement scope.'
                )
            seen_keys.add(scope_key)
