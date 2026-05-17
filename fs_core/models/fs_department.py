# -*- coding: utf-8 -*-
# Part of Flight School Management System

"""Flight School Settings fs department module.

Purpose:
    Defines classes FsDepartment for central settings, shared security groups, departments, and base configuration records.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: base, base_setup, auth_signup.
    All Flight School addons consume the groups, menu roots, and shared settings defined here.
"""
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


DEPARTMENT_CODE_PATTERN = re.compile(r'^[A-Z0-9_-]{2,12}$')


class FsDepartment(models.Model):
    """Departments within the Flight School.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.department``.
        _description (str): Human-readable model label, ``Flight School Department``.

    Related:
        All Flight School addons consume the groups, menu roots, and shared settings defined here.
    """

    _name = 'fs.department'
    _description = 'Flight School Department'
    _order = 'sequence, name'
    _parent_name = 'parent_id'
    _parent_store = True

    name = fields.Char(string='Department Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    manager_id = fields.Many2one('res.users', string='Manager', index=True)
    parent_id = fields.Many2one('fs.department', string='Parent Department', index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('fs.department', 'parent_id', string='Sub-Departments')
    note = fields.Text(string='Note')

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The department code must be unique!',
    )

    @api.model
    def _normalize_write_vals(self, vals):
        """Normalize department identifiers before create/write."""
        normalized = dict(vals)
        if isinstance(normalized.get('code'), str):
            normalized['code'] = normalized['code'].strip().upper()
        return normalized

    @api.model_create_multi
    def create(self, vals_list):
        """Normalize department values before creation."""
        normalized_vals_list = [self._normalize_write_vals(vals) for vals in vals_list]
        return super().create(normalized_vals_list)

    def write(self, vals):
        """Normalize department values before writing."""
        return super().write(self._normalize_write_vals(vals))

    @api.constrains('code')
    def _check_code(self):
        """Validate mandatory stable department code rules."""
        for record in self:
            if not record.code:
                raise ValidationError(_('Department code is required.'))
            if not DEPARTMENT_CODE_PATTERN.fullmatch(record.code):
                raise ValidationError(_(
                    'Department code must be 2-12 characters using uppercase letters, numbers, hyphen, or underscore.'
                ))

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        """Prevent recursive department hierarchies."""
        if self._has_cycle('parent_id'):
            raise ValidationError(_('Department hierarchy cannot contain cycles.'))

    @api.constrains('manager_id')
    def _check_manager_id(self):
        """Ensure department managers are active Flight School users."""
        for record in self:
            manager = record.manager_id
            if not manager:
                continue
            if not manager.active:
                raise ValidationError(_('Department manager must be an active user.'))
            if not manager._has_group('fs_core.group_flight_school_user'):
                raise ValidationError(_('Department manager must have a Flight School role.'))

    @api.onchange('code')
    def _onchange_code(self):
        """Normalize code in forms before saving."""
        if self.code:
            self.code = self.code.strip().upper()
