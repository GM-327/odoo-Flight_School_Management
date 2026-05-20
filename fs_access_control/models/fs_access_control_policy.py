# -*- coding: utf-8 -*-
# Part of Flight School Management System

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class FsAccessPolicy(models.Model):
    """Unified policy model for model, record, field, menu, button, action, and report access."""

    _name = 'fs.access.policy'
    _description = 'Flight School Access Policy'
    _order = 'priority desc, sequence, name'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True, index=True)
    sequence = fields.Integer(default=10)
    policy_type = fields.Selection(
        selection=[
            ('model', 'Model Policy'),
            ('record', 'Record Policy'),
            ('field', 'Field Policy'),
            ('menu', 'Menu Policy'),
            ('button', 'Button Policy'),
            ('action', 'Action Policy'),
            ('report', 'Report Policy'),
        ],
        required=True,
        default='model',
        index=True,
    )
    model_id = fields.Many2one(
        'ir.model',
        index=True,
        ondelete='cascade',
        help='Model controlled by this policy. Leave empty only for global UI policies.',
    )
    model_name = fields.Char(
        string='Technical Model',
        related='model_id.model',
        store=True,
        index=True,
    )
    operation = fields.Selection(
        selection=[
            ('read', 'Read'),
            ('write', 'Write'),
            ('create', 'Create'),
            ('unlink', 'Delete'),
            ('export', 'Export'),
            ('import', 'Import'),
            ('print', 'Print'),
            ('download_attachment', 'Download Attachment'),
            ('confirm', 'Confirm'),
            ('approve', 'Approve'),
            ('cancel', 'Cancel'),
            ('dispatch', 'Dispatch'),
            ('complete', 'Complete'),
            ('recalculate', 'Recalculate'),
            ('archive', 'Archive'),
            ('restore', 'Restore'),
            ('read_field', 'Read Field'),
            ('write_field', 'Write Field'),
            ('mask_field', 'Mask Field'),
            ('show_menu', 'Show Menu'),
            ('open_action', 'Open Action'),
            ('show_button', 'Show Button'),
            ('show_report', 'Show Report'),
            ('manage_policy', 'Manage Policy'),
            ('assign_role', 'Assign Role'),
            ('grant_temporary_access', 'Grant Temporary Access'),
            ('view_audit', 'View Audit'),
            ('simulate_access', 'Simulate Access'),
        ],
        required=True,
        index=True,
    )
    effect = fields.Selection(
        selection=[('allow', 'Allow'), ('deny', 'Deny')],
        required=True,
        default='allow',
        index=True,
    )
    min_level_id = fields.Many2one(
        'fs.access.level',
        string='Minimum Level',
        index=True,
        ondelete='restrict',
    )
    role_id = fields.Many2one(
        'fs.access.role',
        index=True,
        ondelete='restrict',
        help='Optional role requirement. The level requirement still applies when set.',
    )
    department_scope = fields.Selection(
        selection=[
            ('none', 'No Department'),
            ('own', 'Own Records'),
            ('assigned', 'Assigned Department'),
            ('assigned_and_children', 'Assigned and Child Departments'),
            ('global', 'Global'),
        ],
        required=True,
        default='assigned',
        index=True,
    )
    department_field = fields.Char(
        help="Field used to match a record to the user's effective departments.",
    )
    custom_domain = fields.Text(
        help='Optional Odoo domain applied as an additional policy condition.',
    )
    field_name = fields.Char(index=True)
    menu_id = fields.Many2one('ir.ui.menu', index=True, ondelete='cascade')
    button_name = fields.Char(index=True)
    button_method = fields.Char(index=True)
    view_id = fields.Many2one('ir.ui.view', index=True, ondelete='set null')
    action_id = fields.Reference(
        selection=[
            ('ir.actions.act_window', 'Window Action'),
            ('ir.actions.server', 'Server Action'),
            ('ir.actions.report', 'Report Action'),
            ('ir.actions.client', 'Client Action'),
            ('ir.actions.act_url', 'URL Action'),
        ],
        string='Action',
    )
    report_id = fields.Many2one('ir.actions.report', index=True, ondelete='cascade')
    priority = fields.Integer(default=10, index=True)
    valid_from = fields.Datetime(index=True)
    valid_to = fields.Datetime(index=True)
    reason_required = fields.Boolean()
    audit_level = fields.Selection(
        selection=[
            ('none', 'None'),
            ('denied_only', 'Denied Only'),
            ('granted_sensitive', 'Granted Sensitive'),
            ('all', 'All'),
        ],
        default='denied_only',
        required=True,
    )
    description = fields.Text(translate=True)

    _policy_lookup_idx = models.Index(
        '(active, policy_type, model_id, operation, effect, priority, valid_from, valid_to)'
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._log_policy_change('policy_create')
        records._invalidate_policy_cache()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._log_policy_change('policy_write')
        self._invalidate_policy_cache()
        return result

    def unlink(self):
        self._log_policy_change('policy_unlink')
        result = super().unlink()
        self._invalidate_policy_cache()
        return result

    @api.constrains('valid_from', 'valid_to')
    def _check_validity_dates(self):
        for record in self:
            if record.valid_from and record.valid_to and record.valid_to <= record.valid_from:
                raise ValidationError(_('Policy expiry must be after the start date.'))

    @api.constrains('policy_type', 'model_id', 'field_name', 'menu_id', 'button_name', 'button_method', 'report_id')
    def _check_policy_target(self):
        for record in self:
            if record.policy_type in ('model', 'record', 'field', 'action', 'button') and not record.model_id:
                raise ValidationError(_('A model is required for model, record, field, action, and button policies.'))
            if record.policy_type == 'field' and not record.field_name:
                raise ValidationError(_('A field name is required for field policies.'))
            if record.policy_type == 'menu' and not record.menu_id:
                raise ValidationError(_('A menu is required for menu policies.'))
            if record.policy_type == 'button' and not (record.button_name or record.button_method):
                raise ValidationError(_('A button name or method is required for button policies.'))
            if record.policy_type == 'report' and not record.report_id:
                raise ValidationError(_('A report is required for report policies.'))

    @api.constrains('custom_domain')
    def _check_custom_domain(self):
        for record in self.filtered('custom_domain'):
            try:
                domain = safe_eval(record.custom_domain, {'__builtins__': {}})
            except Exception as error:
                raise ValidationError(_('Custom domain is not valid: %s') % error) from error
            if not isinstance(domain, (list, tuple)):
                raise ValidationError(_('Custom domain must evaluate to an Odoo domain list.'))

    def is_current(self):
        self.ensure_one()
        now = fields.Datetime.now()
        return (
            self.active
            and (not self.valid_from or self.valid_from <= now)
            and (not self.valid_to or self.valid_to >= now)
        )

    def _invalidate_policy_cache(self):
        self.env['fs.access.service'].invalidate_security_cache()
        self.env.registry.clear_cache()

    def _log_policy_change(self, event_type):
        service = self.env['fs.access.service']
        for record in self:
            service._log_security_event(
                event_type=event_type,
                target_model=record._name,
                target_res_id=record.id,
                operation='manage_policy',
                decision='allowed',
                policy_id=record.id,
                level_id=record.min_level_id.id,
                reason=record.name,
            )
