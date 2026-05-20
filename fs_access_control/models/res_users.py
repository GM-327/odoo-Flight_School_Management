# -*- coding: utf-8 -*-
# Part of Flight School Management System

from odoo import api, fields, models


class ResUsers(models.Model):
    """Expose dynamic Flight School access summaries on users."""

    _inherit = 'res.users'

    fs_access_assignment_ids = fields.One2many(
        'fs.access.assignment',
        'user_id',
        string='Flight School Access Assignments',
    )
    fs_access_grant_ids = fields.One2many(
        'fs.access.grant',
        'user_id',
        string='Flight School Temporary Grants',
    )
    fs_access_highest_level_id = fields.Many2one(
        'fs.access.level',
        string='Highest Flight School Access Level',
        compute='_compute_fs_access_summary',
    )
    fs_access_department_summary = fields.Char(
        string='Effective Departments',
        compute='_compute_fs_access_summary',
    )
    fs_access_active_grant_count = fields.Integer(
        string='Active Grants',
        compute='_compute_fs_access_summary',
    )
    fs_access_assignment_count = fields.Integer(
        string='Assignments',
        compute='_compute_fs_access_summary',
    )

    @api.depends(
        'fs_access_assignment_ids.active',
        'fs_access_assignment_ids.state',
        'fs_access_assignment_ids.level_id',
        'fs_access_assignment_ids.department_id',
        'fs_access_grant_ids.state',
    )
    def _compute_fs_access_summary(self):
        service = self.env['fs.access.service']
        now = fields.Datetime.now()
        levels = self.env['fs.access.level'].sudo().search([])
        levels_by_rank = {level.rank: level for level in levels}
        Department = self.env['fs.department'].sudo()
        for user in self:
            context = service.get_effective_context(user)
            user.fs_access_highest_level_id = levels_by_rank.get(context['highest_rank'])
            departments = Department.browse(context['department_ids'])
            user.fs_access_department_summary = ', '.join(departments.mapped('display_name')) or 'Global/None'
            user.fs_access_assignment_count = self.env['fs.access.assignment'].sudo().search_count([
                ('user_id', '=', user.id),
                ('active', '=', True),
            ])
            user.fs_access_active_grant_count = self.env['fs.access.grant'].sudo().search_count([
                ('user_id', '=', user.id),
                ('state', '=', 'active'),
                ('valid_from', '<=', now),
                ('valid_to', '>=', now),
            ])

    def action_view_fs_access_assignments(self):
        self.ensure_one()
        return {
            'name': self.env._('Flight School Access Assignments'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.access.assignment',
            'view_mode': 'list,form',
            'domain': [('user_id', '=', self.id)],
            'context': {'default_user_id': self.id},
        }

    def action_view_fs_access_grants(self):
        self.ensure_one()
        return {
            'name': self.env._('Flight School Temporary Grants'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.access.grant',
            'view_mode': 'list,form',
            'domain': [('user_id', '=', self.id)],
            'context': {'default_user_id': self.id},
        }
