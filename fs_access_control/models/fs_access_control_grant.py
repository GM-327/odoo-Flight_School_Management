# -*- coding: utf-8 -*-
# Part of Flight School Management System

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FsAccessGrant(models.Model):
    """Temporary or exceptional access grant."""

    _name = 'fs.access.grant'
    _description = 'Flight School Temporary Access Grant'
    _order = 'valid_to, user_id'

    user_id = fields.Many2one('res.users', required=True, index=True, ondelete='cascade')
    granted_by_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        readonly=True,
        index=True,
        ondelete='set null',
    )
    approved_by_id = fields.Many2one('res.users', index=True, ondelete='set null')
    model_id = fields.Many2one('ir.model', required=True, index=True, ondelete='cascade')
    model_name = fields.Char(
        string='Technical Model',
        related='model_id.model',
        store=True,
        index=True,
    )
    res_id = fields.Integer(index=True)
    department_id = fields.Many2one('fs.department', index=True, ondelete='restrict')
    operation = fields.Selection(
        selection=lambda self: self.env['fs.access.policy']._fields['operation'].selection,
        required=True,
        index=True,
    )
    level_id = fields.Many2one('fs.access.level', required=True, index=True, ondelete='restrict')
    valid_from = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    valid_to = fields.Datetime(required=True, index=True)
    state = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('revoked', 'Revoked'),
        ],
        default='active',
        required=True,
        index=True,
    )
    reason = fields.Text(required=True)
    ticket_reference = fields.Char(index=True)
    revoked_by_id = fields.Many2one('res.users', readonly=True, index=True, ondelete='set null')
    revoked_at = fields.Datetime(readonly=True)

    _grant_lookup_idx = models.Index(
        '(user_id, state, model_id, operation, res_id, department_id, valid_from, valid_to)'
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._log_grant_change('grant_create')
        records._invalidate_grant_users()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._log_grant_change('grant_write')
        self._invalidate_grant_users()
        return result

    def unlink(self):
        raise UserError(_('Temporary grants must be revoked or expired, not deleted.'))

    def action_revoke(self):
        self.write({
            'state': 'revoked',
            'revoked_by_id': self.env.user.id,
            'revoked_at': fields.Datetime.now(),
        })
        return True

    def action_expire(self):
        self.write({'state': 'expired'})
        return True

    @api.model
    def _cron_expire_grants(self):
        now = fields.Datetime.now()
        grants = self.sudo().search([
            ('state', '=', 'active'),
            ('valid_to', '<', now),
        ])
        if grants:
            grants.action_expire()
        return True

    @api.constrains('valid_from', 'valid_to')
    def _check_validity_dates(self):
        for record in self:
            if record.valid_to <= record.valid_from:
                raise ValidationError(_('Grant expiry must be after the start date.'))

    def is_current(self):
        self.ensure_one()
        now = fields.Datetime.now()
        return self.state == 'active' and self.valid_from <= now <= self.valid_to

    def _invalidate_grant_users(self):
        self.env['fs.access.service'].invalidate_security_cache(self.mapped('user_id').ids)

    def _log_grant_change(self, event_type):
        service = self.env['fs.access.service']
        for record in self:
            service._log_security_event(
                event_type=event_type,
                user_id=record.user_id.id,
                target_model=record.model_name,
                target_res_id=record.res_id,
                operation=record.operation,
                decision='allowed',
                grant_id=record.id,
                department_id=record.department_id.id,
                level_id=record.level_id.id,
                reason=record.reason,
            )
