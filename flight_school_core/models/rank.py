# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FsRank(models.Model):
    """Military Rank - Defines military rank hierarchy.
    
    Used for both students (cadets) and instructors (military officers).
    Sequence determines hierarchy (1=lowest, 100=highest).
    """
    _name = 'fs.rank'
    _description = 'Military Rank'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # === Basic Fields ===
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        help="Full rank name, e.g., 'Captain', '2nd Lieutenant'"
    )
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help="Short code, e.g., 'CPT', '2LT', 'CDT'"
    )
    category = fields.Selection(
        selection=[
            ('cadet', 'Cadet/Trainee'),
            ('officer', 'Commissioned Officer'),
            ('nco', 'Non-Commissioned Officer'),
            ('civilian', 'Civilian'),
        ],
        string='Category',
        required=True,
        default='officer',
        tracking=True,
        help="Category of this rank"
    )
    sequence = fields.Integer(
        string='Hierarchy Order',
        default=10,
        help="Hierarchy level: 1=lowest rank, higher=more senior"
    )
    insignia = fields.Binary(
        string='Insignia Image',
        attachment=True,
        help="Upload rank insignia image"
    )
    description = fields.Text(
        string='Description',
        help="Description of this rank"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help="Uncheck to archive this rank"
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The rank code must be unique!'
    )
    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'The rank name must be unique!'
    )

    # === Computed Display Name ===
    def _compute_display_name(self):
        for record in self:
            # Use only the rank code in drop-downs; fall back to name if no code
            record.display_name = record.code or record.name

    # === Constraints ===
    @api.constrains('code')
    def _check_code_uppercase(self):
        """Ensure code is always uppercase."""
        for record in self:
            if record.code and record.code != record.code.upper():
                raise ValidationError(_("The code must be uppercase! Got: %s") % record.code)

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
        """Prevent deletion if assigned to people - archive instead."""
        # This will be enhanced in Phase 2 when student/instructor models exist
        return super().unlink()

    # === Actions ===
    def action_archive(self):
        """Archive this rank."""
        self.write({'active': False})

    def action_unarchive(self):
        """Unarchive this rank."""
        self.write({'active': True})
