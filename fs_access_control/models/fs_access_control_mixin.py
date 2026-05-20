# -*- coding: utf-8 -*-
# Part of Flight School Management System

import functools

from odoo import _, api, models
from odoo.exceptions import AccessError
from odoo.fields import Domain


class FsAccessMixin(models.AbstractModel):
    """Reusable server-side enforcement mixin for protected business models."""

    _name = 'fs.access.mixin'
    _description = 'Flight School Access Enforcement Mixin'

    _fs_access_control_enabled = False
    _fs_access_control_department_field = 'security_department_id'
    _fs_access_control_owner_field = 'security_owner_user_id'
    _fs_access_control_global_model = False
    _fs_access_control_sensitive_fields = []

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, *, active_test=True, bypass_access=False):
        if self._fs_access_should_enforce('read') and not self._fs_access_control_global_model:
            access_domain = self.env['fs.access.service'].domain_for(self.env.user, self._name, 'read')
            domain = Domain.AND([Domain(domain), Domain(access_domain)])
        return super()._search(
            domain,
            offset=offset,
            limit=limit,
            order=order,
            active_test=active_test,
            bypass_access=bypass_access,
        )

    def _check_access(self, operation):
        base_result = super()._check_access(operation)
        if base_result or not self._fs_access_should_enforce(operation):
            return base_result

        service = self.env['fs.access.service']
        if not self:
            if not service.can(self.env.user, self._name, operation):
                return self, functools.partial(self._make_fs_access_error, operation, self)
            return None

        forbidden = self.filtered(
            lambda record: not service.can(self.env.user, self._name, operation, record=record)
        )
        if forbidden:
            return forbidden, functools.partial(self._make_fs_access_error, operation, forbidden)
        return None

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if records._fs_access_should_enforce('create'):
            service = self.env['fs.access.service']
            for record in records:
                service.check(self.env.user, record._name, 'create', record=record)
        return records

    def write(self, vals):
        if self._fs_access_should_enforce('write'):
            service = self.env['fs.access.service']
            service.check_field_write(self.env.user, self._name, set(vals), records=self)
            for record in self:
                service.check(self.env.user, self._name, 'write', record=record)
        return super().write(vals)

    def unlink(self):
        if self._fs_access_should_enforce('unlink'):
            service = self.env['fs.access.service']
            for record in self:
                service.check(self.env.user, self._name, 'unlink', record=record)
        return super().unlink()

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if self._fs_access_should_enforce('show_button') and view_type in ('form', 'list'):
            result['arch'] = self.env['fs.access.service'].filter_view_buttons(
                self.env.user,
                self._name,
                result.get('arch'),
                view_id=view_id,
            )
        return result

    def _fs_access_should_enforce(self, operation):
        return bool(
            self._fs_access_control_enabled
            and not self.env.su
        )

    def _make_fs_access_error(self, operation, records):
        record_names = ', '.join(records.mapped('display_name')[:5]) if records else self._description
        return AccessError(_('Flight School access policy denied %(operation)s on %(model)s: %(records)s') % {
            'operation': operation,
            'model': self._description or self._name,
            'records': record_names,
        })
