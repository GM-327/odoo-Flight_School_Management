# -*- coding: utf-8 -*-
# Part of Flight School Management System

from odoo import fields, models
from odoo.exceptions import AccessError


class FsAccessAuditLog(models.Model):
    """Append-only audit trail for access control changes and decisions."""

    _name = 'fs.access.audit.log'
    _description = 'Flight School Access Audit Log'
    _order = 'create_date desc, id desc'

    event_type = fields.Char(required=True, index=True)
    user_id = fields.Many2one('res.users', index=True, ondelete='set null')
    target_model = fields.Char(index=True)
    target_res_id = fields.Integer(index=True)
    operation = fields.Char(index=True)
    decision = fields.Selection(
        selection=[('allowed', 'Allowed'), ('denied', 'Denied')],
        index=True,
    )
    policy_id = fields.Many2one('fs.access.policy', index=True, ondelete='set null')
    grant_id = fields.Many2one('fs.access.grant', index=True, ondelete='set null')
    department_id = fields.Many2one('fs.department', index=True, ondelete='set null')
    level_id = fields.Many2one('fs.access.level', index=True, ondelete='set null')
    reason = fields.Text()
    ip_address = fields.Char()
    user_agent = fields.Char()

    _audit_lookup_idx = models.Index('(event_type, user_id, target_model, target_res_id, operation, create_date)')

    def write(self, vals):
        raise AccessError(self.env._('Access audit logs are append-only.'))

    def unlink(self):
        raise AccessError(self.env._('Access audit logs are append-only.'))
