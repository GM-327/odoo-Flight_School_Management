# -*- coding: utf-8 -*-
# Part of Flight School Management System

import json

from odoo import fields, models


class FsAccessSimulator(models.TransientModel):
    """Read-only administrator tool for explaining dynamic access decisions."""

    _name = 'fs.access.simulator'
    _description = 'Flight School Access Simulator'

    user_id = fields.Many2one(
        'res.users',
        required=True,
        default=lambda self: self.env.user,
    )
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade')
    model_name = fields.Char(
        string='Technical Model',
        related='model_id.model',
        readonly=True,
    )
    operation = fields.Selection(
        selection=lambda self: self.env['fs.access.policy']._fields['operation'].selection,
        required=True,
        default='read',
    )
    res_id = fields.Integer(string='Record ID')
    field_name = fields.Char()
    menu_id = fields.Many2one('ir.ui.menu', ondelete='set null')
    button_name = fields.Char()
    button_method = fields.Char()
    decision = fields.Selection(
        selection=[('allowed', 'Allowed'), ('denied', 'Denied')],
        readonly=True,
    )
    explanation = fields.Text(readonly=True)

    def action_simulate(self):
        self.ensure_one()
        record = self.env[self.model_name].browse(self.res_id).exists() if self.res_id else None
        explanation = self.env['fs.access.service'].explain(
            self.user_id,
            self.model_name,
            self.operation,
            record=record,
            field_name=self.field_name,
            menu=self.menu_id,
            button_name=self.button_name,
            button_method=self.button_method,
        )
        self.decision = explanation['decision']
        self.explanation = json.dumps(explanation, indent=2, sort_keys=True, default=str)
        self.env['fs.access.service']._log_security_event(
            event_type='simulator_usage',
            user_id=self.env.user.id,
            target_model=self.model_name,
            target_res_id=self.res_id,
            operation='simulate_access',
            decision='allowed',
            policy_id=explanation.get('policy_id'),
            grant_id=explanation.get('grant_id'),
            department_id=explanation.get('department_id'),
            level_id=explanation.get('level_id'),
            reason='Simulated %s for %s' % (self.operation, self.user_id.display_name),
        )
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
