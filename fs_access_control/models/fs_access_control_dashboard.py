# -*- coding: utf-8 -*-
# Part of Flight School Management System

from odoo import api, fields, models


class FsAccessDashboard(models.TransientModel):
    """Administrative dashboard for access control review."""

    _name = 'fs.access.dashboard'
    _description = 'Flight School Access Control Dashboard'

    active_assignment_count = fields.Integer(compute='_compute_counts')
    active_policy_count = fields.Integer(compute='_compute_counts')
    active_grant_count = fields.Integer(compute='_compute_counts')
    conflict_issue_count = fields.Integer(compute='_compute_counts')
    denied_event_count = fields.Integer(compute='_compute_counts')

    @api.depends_context('uid')
    def _compute_counts(self):
        now = fields.Datetime.now()
        Assignment = self.env['fs.access.assignment'].sudo()
        Policy = self.env['fs.access.policy'].sudo()
        Grant = self.env['fs.access.grant'].sudo()
        Conflict = self.env['fs.access.conflict.issue'].sudo()
        Audit = self.env['fs.access.audit.log'].sudo()
        for dashboard in self:
            dashboard.active_assignment_count = Assignment.search_count([
                ('active', '=', True),
                ('state', '=', 'active'),
            ])
            dashboard.active_policy_count = Policy.search_count([('active', '=', True)])
            dashboard.active_grant_count = Grant.search_count([
                ('state', '=', 'active'),
                ('valid_from', '<=', now),
                ('valid_to', '>=', now),
            ])
            dashboard.conflict_issue_count = Conflict.search_count([('active', '=', True)])
            dashboard.denied_event_count = Audit.search_count([
                ('event_type', '=', 'access_denied'),
                ('decision', '=', 'denied'),
            ])

    def action_open_assignments(self):
        return self._window_action('fs.access.assignment', self.env._('User Assignments'))

    def action_open_policies(self):
        return self._window_action('fs.access.policy', self.env._('Policies'))

    def action_open_grants(self):
        return self._window_action('fs.access.grant', self.env._('Temporary Grants'))

    def action_open_conflicts(self):
        return self._window_action('fs.access.conflict.issue', self.env._('Conflict Review'))

    def action_open_audit(self):
        return self._window_action('fs.access.audit.log', self.env._('Audit Log'))

    def _window_action(self, model_name, name):
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': model_name,
            'view_mode': 'list,form',
        }
