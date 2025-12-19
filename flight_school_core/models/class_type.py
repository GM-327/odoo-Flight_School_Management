# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FsClassType(models.Model):
    """Training Class Type - Defines types of training programs.
    
    Examples: PPL (Private Pilot License), CPL (Commercial Pilot License),
    IR (Instrument Rating), etc.
    """
    _name = 'fs.class.type'
    _description = 'Training Class Type'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # === Basic Fields ===
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        help="Full name of the training program, e.g., 'CPL - Commercial Pilot License'"
    )
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help="Short unique code, e.g., 'CPL', 'IR', 'PPL'"
    )
    description = fields.Text(
        string='Description',
        help="Detailed description of this training program"
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help="Color for visual identification in UI"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order in which types are displayed"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help="Uncheck to archive this training type"
    )

    # === Training Parameters ===
    estimated_duration = fields.Integer(
        string='Estimated Duration',
        help="Typical program length"
    )
    estimated_duration_unit = fields.Selection(
        selection=[
            ('weeks', 'Weeks'),
            ('months', 'Months'),
        ],
        string='Duration Unit',
        default='months',
        required=True
    )
    min_flight_hours_required = fields.Float(
        string='Minimum Flight Hours',
        digits=(6, 1),
        help="Minimum flight hours required to complete this program"
    )
    
    # === Regulatory ===
    regulation_reference = fields.Char(
        string='Regulation Reference',
        help="JAR-FCL/EASA regulation reference, e.g., 'JAR-FCL 1.125'"
    )
    is_military = fields.Boolean(
        string='Military Training',
        default=False,
        tracking=True,
        help="Check if this is military-specific training (vs civilian certification)"
    )
    
    # === Prerequisites ===
    prerequisite_type_ids = fields.Many2many(
        comodel_name='fs.class.type',
        relation='fs_class_type_prerequisite_rel',
        column1='class_type_id',
        column2='prerequisite_id',
        string='Prerequisites',
        help="Training class types that must be completed before this one"
    )

    # === SQL Constraints ===
    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The code must be unique!'
    )
    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'The name must be unique!'
    )

    # === Computed Display Name ===
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.code or record.name

    # === Constraints ===
    @api.constrains('code')
    def _check_code_uppercase(self):
        """Ensure code is always uppercase."""
        for record in self:
            if record.code and record.code != record.code.upper():
                raise ValidationError(_("The code must be uppercase! Got: %s") % record.code)

    @api.constrains('prerequisite_type_ids')
    def _check_no_circular_prerequisites(self):
        """Prevent circular prerequisites."""
        for record in self:
            if record in record.prerequisite_type_ids:
                raise ValidationError(_("A training type cannot be a prerequisite of itself!"))
            # Check for deeper circular references
            visited = set()
            to_check = list(record.prerequisite_type_ids)
            while to_check:
                prereq = to_check.pop()
                if prereq.id == record.id:
                    raise ValidationError(_("Circular prerequisite detected!"))
                if prereq.id not in visited:
                    visited.add(prereq.id)
                    to_check.extend(prereq.mapped('prerequisite_type_ids'))

    # === CRUD Overrides ===
    @api.model_create_multi
    def create(self, vals_list):
        """Convert code to uppercase on create."""
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].upper()
        return super().create(vals_list)

    def write(self, vals):
        """Convert code to uppercase on write."""
        if vals.get('code'):
            vals['code'] = vals['code'].upper()
        return super().write(vals)

    def unlink(self):
        """Prevent deletion if training classes exist - archive instead."""
        # This will be enhanced in Phase 2 when training_class model exists
        # For now, allow deletion
        return super().unlink()

    # === Actions ===
    def action_archive(self):
        """Archive this training type."""
        self.write({'active': False})

    def action_unarchive(self):
        """Unarchive this training type."""
        self.write({'active': True})
