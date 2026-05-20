# -*- coding: utf-8 -*-
# Part of Flight School Management System

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FsAccessLevel(models.Model):
    """Hierarchical authority level used by dynamic Flight School policies."""

    _name = 'fs.access.level'
    _description = 'Flight School Access Level'
    _order = 'rank, sequence, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    rank = fields.Integer(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text(translate=True)

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The access level code must be unique!',
    )
    _rank_unique = models.Constraint(
        'UNIQUE(rank)',
        'The access level rank must be unique!',
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
        records._log_access_configuration_change('level_create')
        return records

    def write(self, vals):
        result = super().write(self._normalize_write_vals(vals))
        self._log_access_configuration_change('level_write')
        self.env['fs.access.service'].invalidate_security_cache()
        return result

    def unlink(self):
        self._log_access_configuration_change('level_unlink')
        result = super().unlink()
        self.env['fs.access.service'].invalidate_security_cache()
        return result

    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if not record.code or not record.code.strip():
                raise ValidationError(_('Access level code is required.'))

    @api.constrains('rank')
    def _check_rank(self):
        for record in self:
            if record.rank <= 0:
                raise ValidationError(_('Access level rank must be greater than zero.'))

    def _log_access_configuration_change(self, event_type):
        service = self.env['fs.access.service']
        for record in self:
            service._log_security_event(
                event_type=event_type,
                target_model=record._name,
                target_res_id=record.id,
                operation='manage_policy',
                decision='allowed',
                level_id=record.id,
            )
