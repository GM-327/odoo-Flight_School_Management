# -*- coding: utf-8 -*-
# Part of Flight School Management System

from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestFsAccessControl(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = cls.env['fs.access.service']
        cls.group_user = cls.env.ref('fs_core.group_flight_school_user')
        cls.group_admin = cls.env.ref('fs_core.group_flight_school_admin')
        cls.role_viewer = cls.env.ref('fs_access_control.role_viewer')
        cls.role_user = cls.env.ref('fs_access_control.role_user')
        cls.role_manager = cls.env.ref('fs_access_control.role_department_manager')
        cls.level_operator = cls.env.ref('fs_access_control.level_operator')

        cls.parent_department = cls.env['fs.department'].create({
            'name': 'Access Parent Department',
            'code': 'ACL-PAR',
        })
        cls.child_department = cls.env['fs.department'].create({
            'name': 'Access Child Department',
            'code': 'ACL-CHD',
            'parent_id': cls.parent_department.id,
        })
        cls.other_department = cls.env['fs.department'].create({
            'name': 'Access Other Department',
            'code': 'ACL-OTH',
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Access Control User',
            'login': 'fs.access.user@example.com',
            'group_ids': [(6, 0, [cls.group_user.id])],
        })
        cls.admin_user = cls.env['res.users'].create({
            'name': 'Access Control Admin',
            'login': 'fs.access.admin@example.com',
            'group_ids': [(6, 0, [cls.group_admin.id])],
        })
        cls.department_model = cls.env['ir.model']._get('fs.department')

    def test_default_operator_level_label(self):
        self.assertEqual(self.level_operator.rank, 30)
        self.assertEqual(self.level_operator.name, 'Operator')

    def test_effective_context_includes_child_departments_only_when_configured(self):
        self.env['fs.access.assignment'].create({
            'user_id': self.user.id,
            'role_id': self.role_manager.id,
            'department_id': self.parent_department.id,
            'scope': 'assigned_and_children',
            'state': 'active',
        })

        context = self.service.get_effective_context(self.user)

        self.assertIn(self.parent_department.id, context['department_ids'])
        self.assertIn(self.child_department.id, context['department_ids'])
        self.assertNotIn(self.other_department.id, context['department_ids'])
        self.assertEqual(context['highest_rank'], 40)

    def test_explicit_deny_policy_overrides_allow_policy(self):
        self.env['fs.access.assignment'].create({
            'user_id': self.user.id,
            'role_id': self.role_viewer.id,
            'scope': 'global',
            'state': 'active',
        })
        self.env['fs.access.policy'].create({
            'name': 'Allow department read for viewers',
            'policy_type': 'model',
            'model_id': self.department_model.id,
            'operation': 'read',
            'effect': 'allow',
            'min_level_id': self.role_viewer.level_id.id,
            'department_scope': 'none',
            'priority': 10,
        })
        self.env['fs.access.policy'].create({
            'name': 'Deny department read for viewers',
            'policy_type': 'model',
            'model_id': self.department_model.id,
            'operation': 'read',
            'effect': 'deny',
            'min_level_id': self.role_viewer.level_id.id,
            'department_scope': 'none',
            'priority': 100,
        })

        self.assertFalse(self.service.can(self.user, 'fs.department', 'read', record=self.parent_department))

    def test_temporary_grant_allows_record_specific_operation(self):
        now = fields.Datetime.now()
        self.env['fs.access.grant'].create({
            'user_id': self.user.id,
            'model_id': self.department_model.id,
            'res_id': self.parent_department.id,
            'operation': 'write',
            'level_id': self.role_viewer.level_id.id,
            'valid_from': now,
            'valid_to': now + timedelta(hours=1),
            'reason': 'Temporary department correction.',
        })

        self.assertTrue(self.service.can(self.user, 'fs.department', 'write', record=self.parent_department))
        self.assertFalse(self.service.can(self.user, 'fs.department', 'write', record=self.other_department))

    def test_assignment_write_invalidates_effective_context_cache(self):
        assignment = self.env['fs.access.assignment'].create({
            'user_id': self.user.id,
            'role_id': self.role_viewer.id,
            'scope': 'global',
            'state': 'active',
        })

        self.assertEqual(self.service.get_effective_context(self.user)['highest_rank'], 10)
        assignment.write({'role_id': self.role_user.id})
        self.assertEqual(self.service.get_effective_context(self.user)['highest_rank'], 20)

    def test_menu_policy_uses_bootstrap_admin_group(self):
        menu = self.env.ref('fs_access_control.menu_access_levels')

        self.assertTrue(self.service.can(self.admin_user, False, 'show_menu', menu=menu))
        self.assertFalse(self.service.can(self.user, False, 'show_menu', menu=menu))

    def test_button_policy_decision(self):
        self.env['fs.access.policy'].create({
            'name': 'Show department test button to security admins',
            'policy_type': 'button',
            'model_id': self.department_model.id,
            'operation': 'show_button',
            'effect': 'allow',
            'min_level_id': self.env.ref('fs_access_control.level_security_administrator').id,
            'department_scope': 'global',
            'button_method': 'action_test_button',
            'priority': 90,
        })

        self.assertTrue(self.service.button_visible(
            self.admin_user,
            'fs.department',
            button_method='action_test_button',
        ))
        self.assertFalse(self.service.button_visible(
            self.user,
            'fs.department',
            button_method='action_test_button',
        ))
