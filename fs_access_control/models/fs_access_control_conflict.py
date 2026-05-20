# -*- coding: utf-8 -*-
# Part of Flight School Management System

from collections import defaultdict

from odoo import api, fields, models


class FsAccessConflictIssue(models.Model):
    """Detected policy and grant review issues."""

    _name = 'fs.access.conflict.issue'
    _description = 'Flight School Access Conflict Issue'
    _order = 'severity desc, issue_type, name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    issue_type = fields.Selection(
        selection=[
            ('allow_deny_overlap', 'Allow/Deny Overlap'),
            ('broad_global_policy', 'Broad Global Policy'),
            ('grant_without_expiry', 'Grant Without Expiry'),
            ('menu_without_policy', 'Menu Without Server Policy'),
        ],
        required=True,
        index=True,
    )
    severity = fields.Selection(
        selection=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium',
        required=True,
        index=True,
    )
    model_id = fields.Many2one('ir.model', index=True, ondelete='set null')
    menu_id = fields.Many2one('ir.ui.menu', index=True, ondelete='set null')
    user_id = fields.Many2one('res.users', index=True, ondelete='set null')
    policy_ids = fields.Many2many('fs.access.policy', string='Policies')
    grant_id = fields.Many2one('fs.access.grant', index=True, ondelete='set null')
    description = fields.Text()

    @api.model
    def action_refresh_conflicts(self):
        self.sudo().search([]).unlink()
        self._detect_allow_deny_overlap()
        self._detect_broad_global_policies()
        self._detect_grants_without_expiry()
        self.env['fs.access.service']._log_security_event(
            event_type='conflict_review',
            operation='view_audit',
            decision='allowed',
            reason='Access conflict review refreshed.',
        )
        return {
            'name': self.env._('Conflict Review'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'list,form',
        }

    def _detect_allow_deny_overlap(self):
        grouped_policies = defaultdict(lambda: self.env['fs.access.policy'])
        policies = self.env['fs.access.policy'].sudo().search([('active', '=', True)])
        for policy in policies:
            key = (
                policy.policy_type,
                policy.model_id.id,
                policy.operation,
                policy.department_scope,
                policy.department_field,
                policy.field_name,
                policy.menu_id.id,
                policy.button_name,
                policy.button_method,
                policy.role_id.id,
            )
            grouped_policies[key] |= policy

        for policy_group in grouped_policies.values():
            effects = set(policy_group.mapped('effect'))
            if {'allow', 'deny'} <= effects:
                self.sudo().create({
                    'name': self.env._('Allow and deny policies overlap'),
                    'issue_type': 'allow_deny_overlap',
                    'severity': 'high',
                    'model_id': policy_group[:1].model_id.id,
                    'policy_ids': [(6, 0, policy_group.ids)],
                    'description': self.env._('Policies with the same model, operation, and scope contain both allow and deny effects.'),
                })

    def _detect_broad_global_policies(self):
        sensitive_operations = ('unlink', 'export', 'import', 'grant_temporary_access', 'manage_policy')
        policies = self.env['fs.access.policy'].sudo().search([
            ('active', '=', True),
            ('effect', '=', 'allow'),
            ('department_scope', '=', 'global'),
            ('operation', 'in', sensitive_operations),
        ])
        for policy in policies:
            self.sudo().create({
                'name': self.env._('Broad global sensitive policy'),
                'issue_type': 'broad_global_policy',
                'severity': 'medium',
                'model_id': policy.model_id.id,
                'policy_ids': [(6, 0, [policy.id])],
                'description': self.env._('Global sensitive policies should be reviewed for least privilege.'),
            })

    def _detect_grants_without_expiry(self):
        grants = self.env['fs.access.grant'].sudo().search([
            ('state', '=', 'active'),
            ('valid_to', '=', False),
        ])
        for grant in grants:
            self.sudo().create({
                'name': self.env._('Temporary grant without expiry'),
                'issue_type': 'grant_without_expiry',
                'severity': 'high',
                'model_id': grant.model_id.id,
                'user_id': grant.user_id.id,
                'grant_id': grant.id,
                'description': self.env._('Temporary grants should have an expiry date.'),
            })
