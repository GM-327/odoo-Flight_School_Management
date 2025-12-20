# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsAdminStaff(models.Model):
    """Administrative personnel in the flight school.
    
    All administrative staff are military personnel.
    They may have system access for administrative tasks.
    """
    
    _name = 'fs.admin.staff'
    _description = 'Administrative Staff'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # === Identification ===
    name = fields.Char(
        string='Full Name',
        required=True,
        tracking=True,
    )
    identification_number = fields.Char(
        string='ID Number',
        help="National ID or passport number.",
    )
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
        ],
        string='Gender',
        required=True,
    )
    birth_date = fields.Date(
        string='Date of Birth',
    )
    nationality_id = fields.Many2one(
        comodel_name='res.country',
        string='Nationality',
        default=lambda self: int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.default_country_id', 0)) or False,
    )
    
    # === Military Information ===
    rank_id = fields.Many2one(
        comodel_name='fs.rank',
        string='Rank',
        help="Military rank.",
    )
    service_number = fields.Char(
        string='Service Number',
        help="Military service number.",
    )
    
    # === Contact ===
    phone = fields.Char(
        string='Phone',
    )
    address = fields.Text(
        string='Address',
    )
    
    # === Employment ===
    department = fields.Char(
        string='Department',
    )
    position = fields.Char(
        string='Position',
    )
    
    # === System Access ===
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User Account',
        help="Odoo user account for system access.",
        tracking=True,
    )
    has_user = fields.Boolean(
        string='Has User Account',
        compute='_compute_has_user',
        store=True,
    )
    
    # === Status ===
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    notes = fields.Text(
        string='Notes',
    )
    
    @api.depends('user_id')
    def _compute_has_user(self):
        for record in self:
            record.has_user = bool(record.user_id)
    
    def action_create_user(self):
        """Create an Odoo user account for this person."""
        self.ensure_one()
        if self.user_id:
            from odoo.exceptions import UserError
            raise UserError("This person already has a user account.")
        
        return {
            'name': 'Create User Account',
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.name,
                'default_login': self.name.lower().replace(' ', '.') if self.name else '',
                'default_groups_id': [(4, self.env.ref('fs_core.group_flight_school_user').id)],
            },
        }
    
    def action_view_user(self):
        """Open the linked user account."""
        self.ensure_one()
        if not self.user_id:
            from odoo.exceptions import UserError
            raise UserError("This person does not have a user account.")
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'res_id': self.user_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    _service_number_unique = models.Constraint(
        'UNIQUE(service_number)', 
        'Service number must be unique!',
    )
