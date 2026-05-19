# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People fs person module.

Purpose:
    Defines classes FsPerson for students, instructors, pilots, administrative staff, qualifications, licenses, and medical tracking.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class FsPerson(models.AbstractModel):
    """Abstract base model for all personnel in the flight school system.

    This model is NOT related to res.partner. Personnel data is managed
    independently. Users can optionally be created and linked for system access.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.person``.
        _inherit: Odoo model(s) extended by this class: ``['mail.thread', 'mail.activity.mixin']``.
        _description (str): Human-readable model label, ``Flight School Person (Base)``.

    Related:
        fs_training enrolls people in classes.
        fs_scheduling exposes people through the crew-member SQL view.
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
    rank_code = fields.Char(
        string='Rank',
        related='rank_id.code',
        store=True,
        readonly=True,
        help="Short code of the assigned rank for list displays.",
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

    # === Role Lifecycle ===
    person_identity_id = fields.Many2one(
        comodel_name='fs.person.identity',
        string='Person Identity',
        ondelete='restrict',
        index=True,
        copy=False,
        tracking=True,
        help="Stable identity that groups this role with previous/future roles.",
    )
    role_state = fields.Selection(
        selection=[
            ('current', 'Current'),
            ('former', 'Former'),
        ],
        string='Role Status',
        default='current',
        required=True,
        index=True,
        copy=False,
        tracking=True,
    )
    role_start_date = fields.Date(
        string='Role Start Date',
        default=fields.Date.context_today,
        required=True,
        copy=False,
        tracking=True,
    )
    role_end_date = fields.Date(
        string='Role End Date',
        copy=False,
        tracking=True,
    )
    transition_in_id = fields.Many2one(
        comodel_name='fs.person.role.transition',
        string='Incoming Transition',
        readonly=True,
        copy=False,
        ondelete='restrict',
    )
    transition_out_id = fields.Many2one(
        comodel_name='fs.person.role.transition',
        string='Outgoing Transition',
        readonly=True,
        copy=False,
        ondelete='restrict',
    )
    is_current_role = fields.Boolean(
        string='Is Current Role',
        compute='_compute_is_current_role',
        store=True,
        index=True,
    )
    transition_count = fields.Integer(
        string='Role Transitions',
        compute='_compute_transition_count',
    )

    @api.model
    def _get_role_model_names(self):
        """Return concrete models that participate in flight-role transitions.

        Returns:
            tuple: Supported role model names.
        """
        return ('fs.student', 'fs.pilot', 'fs.instructor')

    @api.model_create_multi
    def create(self, vals_list):
        """Create role records with a stable identity when one is missing.

        Args:
            vals_list: List of value dictionaries passed to the ORM.

        Returns:
            models.Model: Newly created recordset.
        """
        if self._name in self._get_role_model_names():
            Identity = self.env['fs.person.identity']
            for vals in vals_list:
                if not vals.get('person_identity_id'):
                    vals['person_identity_id'] = Identity.create(
                        self._prepare_identity_vals_from_create_vals(vals)
                    ).id
                vals.setdefault('role_start_date', fields.Date.context_today(self))
        return super().create(vals_list)

    @api.model
    def _prepare_identity_vals_from_create_vals(self, vals):
        """Prepare identity values from role create values.

        Args:
            vals: Role create values.

        Returns:
            dict: Values for ``fs.person.identity``.
        """
        return {
            'name': vals.get('name') or self.env._('New Person'),
            'identification_number': vals.get('identification_number'),
            'service_number': vals.get('service_number'),
            'birth_date': vals.get('birth_date'),
            'nationality_id': vals.get('nationality_id'),
        }

    def _prepare_identity_vals_from_record(self):
        """Prepare identity values from an existing role record.

        Returns:
            dict: Values for ``fs.person.identity``.
        """
        self.ensure_one()
        return {
            'name': self.name or self.env._('New Person'),
            'identification_number': self.identification_number,
            'service_number': self.service_number,
            'birth_date': self.birth_date,
            'nationality_id': self.nationality_id.id if self.nationality_id else False,
        }

    def _ensure_person_identity(self):
        """Create missing identity records for existing roles.

        Returns:
            models.Model: The current recordset.
        """
        Identity = self.env['fs.person.identity']
        for record in self:
            if not record.person_identity_id:
                identity = Identity.create(record._prepare_identity_vals_from_record())
                record.write({'person_identity_id': identity.id})
        return self

    @api.depends('active', 'role_state')
    def _compute_is_current_role(self):
        """Compute whether a role is currently operational.

        Returns:
            None: Updates Odoo records in place.
        """
        for record in self:
            record.is_current_role = bool(record.active and record.role_state == 'current')

    @api.depends('person_identity_id.transition_ids')
    def _compute_transition_count(self):
        """Compute transition count for role smart buttons.

        Returns:
            None: Updates Odoo records in place.
        """
        for record in self:
            record.transition_count = len(record.person_identity_id.transition_ids) if record.person_identity_id else 0

    @api.constrains('person_identity_id', 'role_state', 'active')
    def _check_single_current_role_per_identity(self):
        """Ensure one current flight role per identity.

        Returns:
            None: Raises if the identity has multiple current active roles.

        Raises:
            ValidationError: If more than one current role exists for an identity.
        """
        identities = self.mapped('person_identity_id')
        for identity in identities:
            if not identity:
                continue
            current_count = 0
            for model_name in self._get_role_model_names():
                current_count += self.env[model_name].with_context(active_test=False).search_count([
                    ('person_identity_id', '=', identity.id),
                    ('role_state', '=', 'current'),
                    ('active', '=', True),
                ])
            if current_count > 1:
                raise ValidationError(self.env._(
                    'Only one current student, pilot, or instructor role is allowed for the same identity.'
                ))

    @api.constrains('person_identity_id', 'role_state', 'role_start_date', 'role_end_date')
    def _check_role_lifecycle_dates(self):
        """Validate role lifecycle consistency.

        Returns:
            None: Raises on invalid lifecycle values.

        Raises:
            ValidationError: If lifecycle values are inconsistent.
        """
        for record in self:
            if record._name not in record._get_role_model_names():
                continue
            if record.role_state in ('current', 'former') and not record.person_identity_id:
                raise ValidationError(self.env._('A role must be linked to a person identity.'))
            if record.role_state == 'current' and record.role_end_date:
                raise ValidationError(self.env._('A current role cannot have an end date.'))
            if record.role_state == 'former' and not record.role_end_date:
                raise ValidationError(self.env._('A former role must have an end date.'))
            if record.role_start_date and record.role_end_date and record.role_end_date < record.role_start_date:
                raise ValidationError(self.env._('Role end date cannot be before role start date.'))

    def _action_open_role_transition_wizard(self, transition_type):
        """Open the role transition wizard for this role.

        Args:
            transition_type: Supported transition type.

        Returns:
            dict: Odoo action dictionary.
        """
        self.ensure_one()
        self._ensure_person_identity()
        return {
            'name': self.env._('Role Transition'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.person.role.transition.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_source_model': self._name,
                'default_source_res_id': self.id,
                'default_transition_type': transition_type,
            },
        }

    def action_view_person_identity(self):
        """Open the linked person identity.

        Returns:
            dict: Odoo action dictionary.
        """
        self.ensure_one()
        if not self.person_identity_id:
            raise UserError(self.env._('No person identity has been created for this role yet.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fs.person.identity',
            'res_id': self.person_identity_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'active_test': False},
        }

    def action_view_role_transitions(self):
        """Open transition audit records for this role's identity.

        Returns:
            dict: Odoo action dictionary.
        """
        self.ensure_one()
        if not self.person_identity_id:
            raise UserError(self.env._('No person identity has been created for this role yet.'))
        return {
            'name': self.env._('Role Transitions'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.person.role.transition',
            'view_mode': 'list,form',
            'domain': [('person_identity_id', '=', self.person_identity_id.id)],
            'context': {'default_person_identity_id': self.person_identity_id.id},
        }

    @api.depends('medical_expiry')
    def _compute_medical_status(self):
        """Compute medical status based on expiry date and warning period from settings.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
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
        """Compute has user values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.has_user = bool(record.user_id)

    def action_create_user(self):
        """Create an Odoo user account for this person.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.

        Raises:
            UserError: If user-facing business validation fails.
        """
        self.ensure_one()
        if self.user_id:
            raise UserError(self.env._("This person already has a user account."))

        # Open wizard to create user
        return {
            'name': self.env._('Create User Account'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.name,
                'default_login': self._suggest_login(),
                'default_group_ids': [(4, self.env.ref('fs_core.group_flight_school_user').id)],
                'fs_person_id': self.id,
                'fs_person_model': self._name,
            },
        }

    def _suggest_login(self):
        """Suggest a login based on the person's name.

        Returns:
            Any: Value required by the Odoo ORM, action system, or calling workflow.
        """
        if self.name:
            # Convert name to lowercase, replace spaces with dots
            return self.name.lower().replace(' ', '.')
        return ''

    def action_view_user(self):
        """Open the linked user account.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.

        Raises:
            UserError: If user-facing business validation fails.
        """
        self.ensure_one()
        if not self.user_id:
            raise UserError(self.env._("This person does not have a user account."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'res_id': self.user_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
