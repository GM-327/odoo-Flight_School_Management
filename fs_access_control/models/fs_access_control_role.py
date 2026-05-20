# -*- coding: utf-8 -*-
# Part of Flight School Management System

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FsAccessRole(models.Model):
    """Business role mapped to an access level."""

    _name = 'fs.access.role'
    _description = 'Flight School Access Role'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    level_id = fields.Many2one(
        'fs.access.level',
        string='Access Level',
        required=True,
        index=True,
        ondelete='restrict',
    )
    active = fields.Boolean(default=True)
    description = fields.Text(translate=True)
    implied_role_ids = fields.Many2many(
        'fs.access.role',
        'fs_access_role_implied_rel',
        'role_id',
        'implied_role_id',
        string='Implied Roles',
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The access role code must be unique!',
    )


    @api.model
    def _normalize_write_vals(self, vals):
        normalized = dict(vals)
        if isinstance(normalized.get('code'), str):
            normalized['code'] = normalized['code'].strip().upper()
        return normalized

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create([
            self._normalize_write_vals(vals) for vals in vals_list
        ])
        records._log_access_configuration_change('role_create')
        return records

    def write(self, vals):
        result = super().write(self._normalize_write_vals(vals))
        self._log_access_configuration_change('role_write')
        self.env['fs.access.service'].invalidate_security_cache()
        return result

    def unlink(self):
        self._log_access_configuration_change('role_unlink')
        result = super().unlink()
        self.env['fs.access.service'].invalidate_security_cache()
        return result

    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if not record.code or not record.code.strip():
                raise ValidationError(_('Access role code is required.'))

    @api.constrains('implied_role_ids')
    def _check_implied_role_recursion(self):
        for record in self:
            if record in record._get_all_implied_roles():
                raise ValidationError(_('Access roles cannot imply themselves.'))

    def _get_all_implied_roles(self):
        roles = self.env['fs.access.role']
        pending_roles = self.implied_role_ids
        while pending_roles:
            role = pending_roles[0]
            pending_roles -= role
            if role in roles:
                continue
            roles |= role
            pending_roles |= role.implied_role_ids
        return roles

    def _log_access_configuration_change(self, event_type):
        service = self.env['fs.access.service']
        for record in self:
            service._log_security_event(
                event_type=event_type,
                target_model=record._name,
                target_res_id=record.id,
                operation='manage_policy',
                decision='allowed',
                level_id=record.level_id.id,
                reason=record.name,
            )
