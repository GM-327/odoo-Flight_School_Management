# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError


class FsPerson(models.AbstractModel):
    """Abstract base model for all personnel in the flight school system.
    
    This model is NOT related to res.partner. Personnel data is managed
    independently. Users can optionally be created and linked for system access.
    """
    
    _name = 'fs.person'
    _description = 'Flight School Person (Base)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # === Image ===
    image = fields.Image(
        string='Photo',
        max_width=1024,
        max_height=1024,
    )
    image_128 = fields.Image(
        string='Thumbnail',
        related='image',
        max_width=128,
        max_height=128,
        store=True,
    )

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
        tracking=True,
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
    
    # === Contact ===
    phone = fields.Char(
        string='Phone',
    )
    address = fields.Text(
        string='Address',
    )
    
    # === Military Info ===
    is_military = fields.Boolean(
        string='Military Personnel',
        default=True,
        tracking=True,
    )
    rank_id = fields.Many2one(
        comodel_name='fs.rank',
        string='Rank',
        tracking=True,
    )
    service_number = fields.Char(
        string='Service Number',
        help="Military service/personnel number.",
    )
    
    # === Medical ===
    medical_class_id = fields.Many2one(
        comodel_name='fs.medical.class',
        string='Medical Class',
        tracking=True,
    )
    medical_expiry = fields.Date(
        string='Medical Expiry',
        tracking=True,
    )
    medical_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Expiry'),
        ],
        string='Medical Status',
        compute='_compute_medical_status',
        store=True,
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
    
    @api.depends('medical_expiry')
    def _compute_medical_status(self):
        """Compute medical status based on expiry date and warning period from settings."""
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.medical_warning_days', '30'))
        today = fields.Date.context_today(self)
        warning_date = today + timedelta(days=warning_days)
        
        for record in self:
            if not record.medical_expiry:
                record.medical_status = 'no_expiry'
            elif record.medical_expiry < today:
                record.medical_status = 'expired'
            elif record.medical_expiry <= warning_date:
                record.medical_status = 'expiring'
            else:
                record.medical_status = 'valid'
    
    @api.depends('user_id')
    def _compute_has_user(self):
        for record in self:
            record.has_user = bool(record.user_id)
    
    def action_create_user(self):
        """Create an Odoo user account for this person."""
        self.ensure_one()
        if self.user_id:
            raise UserError("This person already has a user account.")
        
        # Open wizard to create user
        return {
            'name': 'Create User Account',
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.name,
                'default_login': self._suggest_login(),
                'default_groups_id': [(4, self.env.ref('fs_core.group_flight_school_user').id)],
                'fs_person_id': self.id,
                'fs_person_model': self._name,
            },
        }
    
    def _suggest_login(self):
        """Suggest a login based on the person's name."""
        if self.name:
            # Convert name to lowercase, replace spaces with dots
            return self.name.lower().replace(' ', '.')
        return ''
    
    def action_view_user(self):
        """Open the linked user account."""
        self.ensure_one()
        if not self.user_id:
            raise UserError("This person does not have a user account.")
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'res_id': self.user_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
