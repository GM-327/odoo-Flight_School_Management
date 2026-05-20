# -*- coding: utf-8 -*-
# Part of Flight School Management System

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FsAccessAssignment(models.Model):
    """Assign a business role to a user for a department scope."""

    _name = 'fs.access.assignment'
    _description = 'Flight School Access Assignment'
    _order = 'user_id, department_id, role_id'

    user_id = fields.Many2one(
        'res.users',
        required=True,
        index=True,
        ondelete='cascade',
    )
    role_id = fields.Many2one(
        'fs.access.role',
        required=True,
        index=True,
        ondelete='restrict',
    )
    level_id = fields.Many2one(
        'fs.access.level',
        related='role_id.level_id',
        store=True,
        readonly=True,
        index=True,
    )
    department_id = fields.Many2one(
        'fs.department',
        index=True,
        ondelete='restrict',
    )
    include_child_departments = fields.Boolean()
    scope = fields.Selection(
        selection=[
            ('own', 'Own Records'),
            ('assigned', 'Assigned Department'),
            ('assigned_and_children', 'Assigned and Child Departments'),
            ('global', 'Global'),
        ],
        default='assigned',
        required=True,
        index=True,
    )
    valid_from = fields.Datetime(index=True)
    valid_to = fields.Datetime(index=True)
    active = fields.Boolean(default=True, index=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('revoked', 'Revoked'),
        ],
        default='draft',
        required=True,
        index=True,
    )
    assignment_type = fields.Selection(
        selection=[
            ('permanent', 'Permanent'),
            ('temporary', 'Temporary'),
            ('delegated', 'Delegated'),
            ('break_glass', 'Break Glass'),
        ],
        default='permanent',
        required=True,
        index=True,
    )
    assigned_by_id = fields.Many2one(
        'res.users',
        string='Assigned By',
        readonly=True,
        index=True,
        ondelete='set null',
    )
    reason = fields.Text()

    _assignment_lookup_idx = models.Index(
        '(user_id, state, active, department_id, valid_from, valid_to)'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault('assigned_by_id', self.env.user.id)
        records = super().create(vals_list)
        records._log_assignment_change('assignment_create')
        records._invalidate_assignment_users()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._log_assignment_change('assignment_write')
        self._invalidate_assignment_users()
        return result

    def unlink(self):
        protected_assignments = self.filtered(lambda assignment: assignment.state != 'draft')
        if protected_assignments:
            raise UserError(_('Revoke or expire non-draft assignments instead of deleting them.'))
        self._log_assignment_change('assignment_unlink')
        users = self.mapped('user_id')
        result = super().unlink()
        self.env['fs.access.service'].invalidate_security_cache(users.ids)
        return result

    def action_activate(self):
        self.write({'state': 'active', 'active': True})
        return True

    def action_revoke(self):
        self.write({'state': 'revoked', 'active': False})
        return True

    def action_expire(self):
        self.write({'state': 'expired', 'active': False})
        return True

    @api.constrains('valid_from', 'valid_to')
    def _check_validity_dates(self):
        for record in self:
            if record.valid_from and record.valid_to and record.valid_to <= record.valid_from:
                raise ValidationError(_('Assignment expiry must be after the start date.'))

    @api.constrains('scope', 'department_id')
    def _check_department_scope(self):
        for record in self:
            if record.scope != 'global' and not record.department_id:
                raise ValidationError(_('Department is required unless the assignment scope is global.'))

    def _invalidate_assignment_users(self):
        self.env['fs.access.service'].invalidate_security_cache(self.mapped('user_id').ids)

    def _log_assignment_change(self, event_type):
        service = self.env['fs.access.service']
        for record in self:
            service._log_security_event(
                event_type=event_type,
                user_id=record.user_id.id,
                target_model=record._name,
                target_res_id=record.id,
                operation='assign_role',
                decision='allowed',
                department_id=record.department_id.id,
                level_id=record.level_id.id,
                reason=record.reason or record.role_id.display_name,
            )
