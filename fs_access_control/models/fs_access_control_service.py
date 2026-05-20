# -*- coding: utf-8 -*-
# Part of Flight School Management System

from lxml import etree

from odoo import SUPERUSER_ID, _, api, fields, models, tools
from odoo.exceptions import AccessError
from odoo.fields import Domain
from odoo.http import request
from odoo.tools.safe_eval import safe_eval


ACCESS_ADMIN_OPERATIONS = {
    'manage_policy',
    'assign_role',
    'grant_temporary_access',
    'view_audit',
    'simulate_access',
}
UI_OPERATIONS = {'show_menu', 'open_action', 'show_button', 'show_report'}


class FsAccessService(models.AbstractModel):
    """Central dynamic access decision service for Flight School modules."""

    _name = 'fs.access.service'
    _description = 'Flight School Access Control Service'

    @api.model
    def get_effective_context(self, user):
        """Return cached role, rank, and department scope for a user."""
        user = self._coerce_user(user)
        context = self._get_effective_context_cached(user.id)
        return {
            key: value.copy() if isinstance(value, dict) else list(value) if isinstance(value, list) else value
            for key, value in context.items()
        }

    @api.model
    @tools.ormcache('user_id')
    def _get_effective_context_cached(self, user_id):
        user = self.env['res.users'].sudo().browse(user_id).exists()
        if not user or not user.active:
            return self._empty_effective_context(user_id)

        now = fields.Datetime.now()
        assignments = self.env['fs.access.assignment'].sudo().search([
            ('user_id', '=', user.id),
            ('user_id.active', '=', True),
            ('active', '=', True),
            ('state', '=', 'active'),
            '|', ('valid_from', '=', False), ('valid_from', '<=', now),
            '|', ('valid_to', '=', False), ('valid_to', '>=', now),
        ])

        department_rank_by_id = {}
        assignment_department_ids = set()
        global_rank = 0
        highest_rank = 0
        role_ids = set()
        level_ids = set()
        Department = self.env['fs.department'].sudo()

        for assignment in assignments:
            roles = assignment.role_id | assignment.role_id._get_all_implied_roles()
            role_ids.update(roles.ids)
            level_ids.update(roles.mapped('level_id').ids)

            rank = assignment.level_id.rank or 0
            highest_rank = max(highest_rank, rank)
            if assignment.scope == 'global':
                global_rank = max(global_rank, rank)
                continue

            department = assignment.department_id
            if not department:
                continue
            scoped_departments = department
            if assignment.include_child_departments or assignment.scope == 'assigned_and_children':
                scoped_departments = Department.search([('id', 'child_of', department.id)])
            for scoped_department in scoped_departments:
                assignment_department_ids.add(scoped_department.id)
                department_rank_by_id[scoped_department.id] = max(
                    department_rank_by_id.get(scoped_department.id, 0),
                    rank,
                )

        return {
            'user_id': user.id,
            'assignment_ids': assignments.ids,
            'role_ids': sorted(role_ids),
            'level_ids': sorted(level_ids),
            'department_ids': sorted(assignment_department_ids),
            'department_rank_by_id': department_rank_by_id,
            'global_rank': global_rank,
            'highest_rank': highest_rank,
        }

    @api.model
    def can(self, user, model_name, operation, record=None, field_name=None, **kwargs):
        """Return whether the user can perform an operation."""
        if record and len(record) > 1:
            return all(
                self.can(user, model_name, operation, record=single_record, field_name=field_name, **kwargs)
                for single_record in record
            )
        return self.explain(
            user,
            model_name,
            operation,
            record=record,
            field_name=field_name,
            **kwargs,
        )['decision'] == 'allowed'

    @api.model
    def check(self, user, model_name, operation, record=None, field_name=None, **kwargs):
        """Raise AccessError when the dynamic policy layer denies access."""
        explanation = self.explain(
            user,
            model_name,
            operation,
            record=record,
            field_name=field_name,
            **kwargs,
        )
        if explanation['decision'] == 'allowed':
            return True

        target_res_id = record.id if record and len(record) == 1 else False
        self._log_security_event(
            event_type='access_denied',
            user_id=self._coerce_user(user).id,
            target_model=model_name,
            target_res_id=target_res_id,
            operation=operation,
            decision='denied',
            policy_id=explanation.get('policy_id'),
            grant_id=explanation.get('grant_id'),
            department_id=explanation.get('department_id'),
            level_id=explanation.get('level_id'),
            reason=explanation.get('reason'),
        )
        raise AccessError(explanation['reason'])

    @api.model
    def explain(self, user, model_name, operation, record=None, field_name=None, **kwargs):
        """Explain why an operation is allowed or denied."""
        user = self._coerce_user(user)
        if self._is_system_bypass(user):
            return self._decision('allowed', _('System or superuser bypass.'), user=user)

        if record and len(record) > 1:
            explanations = [
                self.explain(user, model_name, operation, record=single_record, field_name=field_name, **kwargs)
                for single_record in record
            ]
            denied = next((explanation for explanation in explanations if explanation['decision'] == 'denied'), None)
            return denied or self._decision('allowed', _('All records are allowed.'), user=user)

        context = self.get_effective_context(user)
        policies = self._candidate_policies(model_name, operation, field_name=field_name, **kwargs)

        for policy in policies.filtered(lambda candidate: candidate.effect == 'deny'):
            if self._policy_matches_user(policy, user, context, model_name, operation, record, field_name, **kwargs):
                return self._decision(
                    'denied',
                    _('Explicit deny policy: %s') % policy.display_name,
                    user=user,
                    policy=policy,
                    record=record,
                )

        grant = self._matching_grant(user, model_name, operation, record=record)
        if grant:
            self._log_security_event(
                event_type='grant_used',
                user_id=user.id,
                target_model=model_name,
                target_res_id=record.id if record else False,
                operation=operation,
                decision='allowed',
                grant_id=grant.id,
                department_id=grant.department_id.id,
                level_id=grant.level_id.id,
                reason=grant.reason,
            )
            return self._decision(
                'allowed',
                _('Temporary grant: %s') % grant.display_name,
                user=user,
                grant=grant,
                record=record,
            )

        for policy in policies.filtered(lambda candidate: candidate.effect == 'allow'):
            if self._policy_matches_user(policy, user, context, model_name, operation, record, field_name, **kwargs):
                return self._decision(
                    'allowed',
                    _('Allowed by policy: %s') % policy.display_name,
                    user=user,
                    policy=policy,
                    record=record,
                )

        return self._decision(
            'denied',
            _('No active allow policy or temporary grant matched.'),
            user=user,
            record=record,
        )

    @api.model
    def domain_for(self, user, model_name, operation='read'):
        """Return a searchable domain for records visible to a user."""
        user = self._coerce_user(user)
        if self._is_system_bypass(user):
            return []

        context = self.get_effective_context(user)
        policies = self._candidate_policies(model_name, operation).filtered(
            lambda policy: policy.policy_type in ('model', 'record')
        )
        deny_policies = policies.filtered(lambda policy: policy.effect == 'deny')
        for policy in deny_policies:
            if (
                policy.department_scope in ('none', 'global')
                and not policy.custom_domain
                and self._policy_matches_user(policy, user, context, model_name, operation)
            ):
                return list(Domain.FALSE)

        allow_domains = []
        for grant in self._matching_grants(user, model_name, operation):
            grant_domain = self._grant_domain(model_name, grant)
            if grant_domain is Domain.TRUE:
                return []
            if grant_domain is not Domain.FALSE:
                allow_domains.append(grant_domain)

        for policy in policies.filtered(lambda candidate: candidate.effect == 'allow'):
            policy_domain = self._policy_domain(policy, user, context, model_name, operation)
            if policy_domain is Domain.TRUE:
                return []
            if policy_domain is not Domain.FALSE:
                allow_domains.append(policy_domain)

        if not allow_domains:
            return list(Domain.FALSE)
        return list(Domain.OR(allow_domains))

    @api.model
    def visible_menus(self, user, menus):
        """Apply configured menu policies to a native Odoo visible menu recordset."""
        if not menus:
            return menus
        controlled_menu_ids = set(self.env['fs.access.policy'].sudo().search([
            ('active', '=', True),
            ('policy_type', '=', 'menu'),
            ('operation', '=', 'show_menu'),
            ('menu_id', 'in', menus.ids),
        ]).mapped('menu_id').ids)
        if not controlled_menu_ids:
            return menus
        allowed_menus = self.env['ir.ui.menu']
        for menu in menus:
            if menu.id not in controlled_menu_ids:
                allowed_menus |= menu
                continue
            model_name = self._model_name_from_menu(menu)
            if self.can(user, model_name, 'show_menu', menu=menu):
                allowed_menus |= menu
        return allowed_menus

    @api.model
    def button_visible(self, user, model_name, button_name=None, button_method=None, view_id=None):
        """Return whether a configured button should be visible."""
        if not self._button_policy_controlled(model_name, button_name, button_method, view_id):
            return True
        return self.can(
            user,
            model_name,
            'show_button',
            button_name=button_name,
            button_method=button_method,
            view_id=view_id,
        )

    @api.model
    def filter_view_buttons(self, user, model_name, arch, view_id=None):
        """Remove buttons denied by active button policies from a view architecture."""
        if not arch or not self.env['fs.access.policy'].sudo().search_count([
            ('active', '=', True),
            ('policy_type', '=', 'button'),
            ('operation', '=', 'show_button'),
            ('model_id.model', '=', model_name),
        ]):
            return arch

        try:
            root = etree.fromstring(arch.encode('utf-8'))
        except etree.XMLSyntaxError:
            return arch

        changed = False
        for button in root.xpath('.//button'):
            button_method = button.get('name') if button.get('type') == 'object' else False
            button_name = button.get('string') or button.get('name')
            if not self.button_visible(user, model_name, button_name, button_method, view_id=view_id):
                parent = button.getparent()
                if parent is not None:
                    parent.remove(button)
                    changed = True
        return etree.tostring(root, encoding='unicode') if changed else arch

    @api.model
    def check_field_write(self, user, model_name, field_names, records=None):
        """Check only configured field write policies; uncontrolled fields remain governed by model write."""
        controlled_fields = self.env['fs.access.policy'].sudo().search([
            ('active', '=', True),
            ('policy_type', '=', 'field'),
            ('operation', '=', 'write_field'),
            ('model_id.model', '=', model_name),
            ('field_name', 'in', list(field_names)),
        ]).mapped('field_name')
        for field_name in controlled_fields:
            target_records = records or self.env[model_name]
            if target_records:
                for record in target_records:
                    self.check(user, model_name, 'write_field', record=record, field_name=field_name)
            else:
                self.check(user, model_name, 'write_field', field_name=field_name)
        return True

    @api.model
    def invalidate_security_cache(self, user_ids=None):
        """Invalidate cached effective access contexts and menu caches."""
        self.env.registry.clear_cache()
        return True

    @api.model
    def _candidate_policies(self, model_name, operation, field_name=None, **kwargs):
        model = self.env['ir.model']._get(model_name) if model_name else self.env['ir.model']
        now = fields.Datetime.now()
        domain = [
            ('active', '=', True),
            ('operation', '=', operation),
            '|', ('valid_from', '=', False), ('valid_from', '<=', now),
            '|', ('valid_to', '=', False), ('valid_to', '>=', now),
        ]
        policy_types = self._policy_types_for_operation(operation)
        if policy_types:
            domain.append(('policy_type', 'in', policy_types))
        if model:
            domain.extend(['|', ('model_id', '=', False), ('model_id', '=', model.id)])
        elif operation not in UI_OPERATIONS:
            domain.append(('model_id', '=', False))
        if field_name:
            domain.append(('field_name', '=', field_name))
        if kwargs.get('menu'):
            domain.append(('menu_id', '=', kwargs['menu'].id))
        if kwargs.get('report'):
            domain.append(('report_id', '=', kwargs['report'].id))
        if kwargs.get('button_name'):
            domain.extend(['|', ('button_name', '=', kwargs['button_name']), ('button_name', '=', False)])
        if kwargs.get('button_method'):
            domain.extend(['|', ('button_method', '=', kwargs['button_method']), ('button_method', '=', False)])
        return self.env['fs.access.policy'].sudo().search(domain, order='priority desc, id')

    @api.model
    def _policy_types_for_operation(self, operation):
        if operation in ('read', 'write', 'create', 'unlink'):
            return ('model', 'record')
        if operation in ('read_field', 'write_field', 'mask_field'):
            return ('field',)
        if operation == 'show_menu':
            return ('menu',)
        if operation == 'show_button':
            return ('button',)
        if operation == 'show_report':
            return ('report',)
        if operation == 'open_action':
            return ('action', 'menu')
        return ('action', 'model', 'record')

    @api.model
    def _policy_matches_user(self, policy, user, context, model_name, operation, record=None, field_name=None, **kwargs):
        if policy.role_id and policy.role_id.id not in context['role_ids']:
            return False
        if field_name and policy.field_name and policy.field_name != field_name:
            return False
        if kwargs.get('menu') and policy.menu_id and policy.menu_id != kwargs['menu']:
            return False
        if kwargs.get('button_name') and policy.button_name and policy.button_name != kwargs['button_name']:
            return False
        if kwargs.get('button_method') and policy.button_method and policy.button_method != kwargs['button_method']:
            return False
        if policy.custom_domain and record and not self._record_matches_custom_domain(record, policy.custom_domain):
            return False

        department_id = self._record_department_id(record, policy) if record else False
        if policy.department_scope == 'global':
            return self._rank_satisfies(user, context, policy, model_name, operation, context['global_rank'])
        if policy.department_scope == 'none':
            return self._rank_satisfies(user, context, policy, model_name, operation, context['highest_rank'])
        if policy.department_scope == 'own':
            if record and not self._record_owned_by_user(record, user):
                return False
            return self._rank_satisfies(user, context, policy, model_name, operation, context['highest_rank'])
        if not record:
            rank = max(context['department_rank_by_id'].values() or [0])
            return self._rank_satisfies(user, context, policy, model_name, operation, rank)
        if not department_id:
            return False
        rank = context['department_rank_by_id'].get(department_id, 0)
        return self._rank_satisfies(user, context, policy, model_name, operation, rank)

    @api.model
    def _rank_satisfies(self, user, context, policy, model_name, operation, rank):
        required_rank = policy.min_level_id.rank if policy.min_level_id else 0
        bootstrap_rank = self._bootstrap_rank(user, model_name, operation, policy.policy_type)
        return max(rank, bootstrap_rank) >= required_rank

    @api.model
    def _bootstrap_rank(self, user, model_name, operation, policy_type=None):
        if user.id == SUPERUSER_ID or not user.has_group('fs_core.group_flight_school_admin'):
            return 0
        if model_name and model_name.startswith('fs.access.'):
            return 90
        if operation in ACCESS_ADMIN_OPERATIONS:
            return 90
        if policy_type in ('menu', 'button', 'action') and operation in UI_OPERATIONS:
            return 90
        return 0

    @api.model
    def _matching_grant(self, user, model_name, operation, record=None):
        return self._matching_grants(user, model_name, operation, record=record, limit=1)[:1]

    @api.model
    def _matching_grants(self, user, model_name, operation, record=None, limit=None):
        model = self.env['ir.model']._get(model_name) if model_name else self.env['ir.model']
        if not model:
            return self.env['fs.access.grant']
        now = fields.Datetime.now()
        grants = self.env['fs.access.grant'].sudo().search([
            ('user_id', '=', user.id),
            ('state', '=', 'active'),
            ('model_id', '=', model.id),
            ('operation', '=', operation),
            ('valid_from', '<=', now),
            ('valid_to', '>=', now),
        ], order='res_id desc, valid_to', limit=limit)
        if not record:
            return grants
        department_id = self._record_department_id(record)
        return grants.filtered(
            lambda grant: (not grant.res_id or grant.res_id == record.id)
            and (not grant.department_id or grant.department_id.id == department_id)
        )

    @api.model
    def _policy_domain(self, policy, user, context, model_name, operation):
        if not self._policy_matches_user(policy, user, context, model_name, operation):
            return Domain.FALSE
        if policy.department_scope in ('none', 'global'):
            return self._custom_domain(policy)

        model = self.env.get(model_name)
        if not model:
            return Domain.FALSE
        if policy.department_scope == 'own':
            owner_field = getattr(model, '_fs_access_control_owner_field', 'security_owner_user_id')
            if owner_field in model._fields:
                base_domain = Domain(owner_field, '=', user.id)
            else:
                base_domain = Domain('create_uid', '=', user.id)
            return base_domain & self._custom_domain(policy)

        department_field = policy.department_field or getattr(
            model,
            '_fs_access_control_department_field',
            'security_department_id' if 'security_department_id' in model._fields else 'department_id',
        )
        if department_field not in model._fields:
            return Domain.FALSE
        department_ids = [
            department_id for department_id, rank in context['department_rank_by_id'].items()
            if self._rank_satisfies(user, context, policy, model_name, operation, rank)
        ]
        if not department_ids:
            return Domain.FALSE
        return Domain(department_field, 'in', department_ids) & self._custom_domain(policy)

    @api.model
    def _grant_domain(self, model_name, grant):
        if grant.res_id:
            return Domain('id', '=', grant.res_id)
        if not grant.department_id:
            return Domain.TRUE
        model = self.env.get(model_name)
        if not model:
            return Domain.FALSE
        department_field = getattr(
            model,
            '_fs_access_control_department_field',
            'security_department_id' if 'security_department_id' in model._fields else 'department_id',
        )
        if department_field not in model._fields:
            return Domain.FALSE
        return Domain(department_field, '=', grant.department_id.id)

    @api.model
    def _custom_domain(self, policy):
        if not policy.custom_domain:
            return Domain.TRUE
        return Domain(safe_eval(policy.custom_domain, {'__builtins__': {}}))

    @api.model
    def _record_matches_custom_domain(self, record, custom_domain):
        try:
            domain = safe_eval(custom_domain, {'__builtins__': {}})
        except Exception:
            return False
        return bool(record.sudo().filtered_domain(domain))

    @api.model
    def _record_department_id(self, record, policy=None):
        if not record:
            return False
        field_name = policy.department_field if policy and policy.department_field else getattr(
            record,
            '_fs_access_control_department_field',
            'security_department_id' if 'security_department_id' in record._fields else 'department_id',
        )
        if field_name not in record._fields:
            return False
        value = record.sudo()[field_name]
        if hasattr(value, 'id'):
            return value.id
        return value or False

    @api.model
    def _record_owned_by_user(self, record, user):
        owner_field = getattr(record, '_fs_access_control_owner_field', 'security_owner_user_id')
        if owner_field in record._fields:
            owner = record.sudo()[owner_field]
            return bool(owner and owner.id == user.id)
        return record.sudo().create_uid.id == user.id

    @api.model
    def _button_policy_controlled(self, model_name, button_name=None, button_method=None, view_id=None):
        domain = [
            ('active', '=', True),
            ('policy_type', '=', 'button'),
            ('operation', '=', 'show_button'),
            ('model_id.model', '=', model_name),
        ]
        if button_name:
            domain.extend(['|', ('button_name', '=', button_name), ('button_name', '=', False)])
        if button_method:
            domain.extend(['|', ('button_method', '=', button_method), ('button_method', '=', False)])
        if view_id:
            domain.extend(['|', ('view_id', '=', view_id), ('view_id', '=', False)])
        return bool(self.env['fs.access.policy'].sudo().search_count(domain))

    @api.model
    def _model_name_from_menu(self, menu):
        action = menu.action
        if not action:
            return False
        if action._name == 'ir.actions.act_window':
            return action.res_model
        if action._name == 'ir.actions.report':
            return action.model
        if action._name == 'ir.actions.server':
            return action.model_name
        return False

    @api.model
    def _decision(self, decision, reason, user=None, policy=None, grant=None, record=None):
        return {
            'decision': decision,
            'reason': reason,
            'user_id': user.id if user else False,
            'policy_id': policy.id if policy else False,
            'grant_id': grant.id if grant else False,
            'department_id': self._record_department_id(record, policy) if record else False,
            'level_id': policy.min_level_id.id if policy and policy.min_level_id else grant.level_id.id if grant else False,
        }

    @api.model
    def _is_system_bypass(self, user):
        return (
            user.id == SUPERUSER_ID
            or (self.env.su and self.env.user.id == user.id)
            or bool(self.env.context.get('fs_access_trusted_system'))
        )

    @api.model
    def _coerce_user(self, user):
        if not user:
            return self.env.user
        if isinstance(user, int):
            return self.env['res.users'].browse(user)
        return user

    @api.model
    def _empty_effective_context(self, user_id):
        return {
            'user_id': user_id,
            'assignment_ids': [],
            'role_ids': [],
            'level_ids': [],
            'department_ids': [],
            'department_rank_by_id': {},
            'global_rank': 0,
            'highest_rank': 0,
        }

    @api.model
    def _log_security_event(self, event_type, user_id=None, target_model=None, target_res_id=None,
                            operation=None, decision=None, policy_id=None, grant_id=None,
                            department_id=None, level_id=None, reason=None):
        request_ip = False
        request_user_agent = False
        if request and getattr(request, 'httprequest', None):
            request_ip = request.httprequest.remote_addr
            request_user_agent = request.httprequest.user_agent.string
        self.env['fs.access.audit.log'].sudo().create({
            'event_type': event_type,
            'user_id': user_id or self.env.user.id,
            'target_model': target_model,
            'target_res_id': target_res_id or 0,
            'operation': operation,
            'decision': decision,
            'policy_id': policy_id or False,
            'grant_id': grant_id or False,
            'department_id': department_id or False,
            'level_id': level_id or False,
            'reason': reason,
            'ip_address': request_ip,
            'user_agent': request_user_agent,
        })
