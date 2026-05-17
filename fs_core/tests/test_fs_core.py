from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestFsCore(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref('fs_core.group_flight_school_user')
        cls.group_manager = cls.env.ref('fs_core.group_flight_school_manager')
        cls.group_admin = cls.env.ref('fs_core.group_flight_school_admin')

        cls.manager_user = cls.env['res.users'].create({
            'name': 'FS Core Manager',
            'login': 'fs.core.manager@example.com',
            'group_ids': [(6, 0, [cls.group_manager.id])],
        })
        cls.admin_user = cls.env['res.users'].create({
            'name': 'FS Core Administrator',
            'login': 'fs.core.admin@example.com',
            'group_ids': [(6, 0, [cls.group_admin.id])],
        })

    def test_department_code_is_required_and_normalized(self):
        department = self.env['fs.department'].create({
            'name': 'Test Operations',
            'code': ' ops-test ',
        })

        self.assertEqual(department.code, 'OPS-TEST')

        with self.assertRaises(ValidationError):
            self.env['fs.department'].create({
                'name': 'Missing Code Department',
                'code': ' ',
            })

    def test_department_code_rejects_invalid_format(self):
        with self.assertRaises(ValidationError):
            self.env['fs.department'].create({
                'name': 'Invalid Code Department',
                'code': 'invalid code',
            })

    def test_department_code_is_unique(self):
        self.env['fs.department'].create({
            'name': 'Unique Department One',
            'code': 'UNIQ',
        })

        with self.assertRaises(ValidationError):
            self.env['fs.department'].create({
                'name': 'Unique Department Two',
                'code': 'UNIQ',
            })

    def test_department_hierarchy_rejects_cycles(self):
        parent = self.env['fs.department'].create({
            'name': 'Parent Department',
            'code': 'PARENT',
        })
        child = self.env['fs.department'].create({
            'name': 'Child Department',
            'code': 'CHILD',
            'parent_id': parent.id,
        })

        with self.assertRaises(ValidationError):
            parent.write({'parent_id': child.id})

    def test_department_manager_must_have_flight_school_role(self):
        internal_user = self.env['res.users'].create({
            'name': 'Non FS Manager',
            'login': 'non.fs.manager@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        with self.assertRaises(ValidationError):
            self.env['fs.department'].create({
                'name': 'Managed Department',
                'code': 'MNGD',
                'manager_id': internal_user.id,
            })

    def test_settings_home_base_is_normalized_and_persisted(self):
        settings = self.env['res.config.settings'].create({
            'fs_default_home_base': ' dtta ',
        })

        self.assertEqual(settings.fs_default_home_base, 'DTTA')
        settings.set_values()

        value = self.env['ir.config_parameter'].sudo().get_param('flight_school.default_home_base')
        self.assertEqual(value, 'DTTA')

    def test_settings_home_base_rejects_invalid_icao_code(self):
        with self.assertRaises(ValidationError):
            self.env['res.config.settings'].create({
                'fs_default_home_base': '1234',
            })

    def test_manager_has_no_sensitive_administration_access(self):
        self.assertFalse(self.env['res.users'].with_user(self.manager_user).has_access('create'))
        self.assertFalse(self.env['res.users'].with_user(self.manager_user).has_access('write'))
        self.assertFalse(self.env['res.groups'].with_user(self.manager_user).has_access('write'))
        self.assertFalse(self.env['res.groups.privilege'].with_user(self.manager_user).has_access('write'))
        self.assertFalse(self.env['res.config.settings'].with_user(self.manager_user).has_access('create'))

    def test_manager_sensitive_writes_raise_access_error(self):
        with self.assertRaises(AccessError):
            self.env['res.users'].with_user(self.manager_user).create({
                'name': 'Forbidden User',
                'login': 'forbidden.user@example.com',
            })

        with self.assertRaises(AccessError):
            self.group_user.with_user(self.manager_user).write({'comment': 'Forbidden update'})

    def test_admin_has_flight_school_administration_access(self):
        self.assertTrue(self.env['res.users'].with_user(self.admin_user).has_access('create'))
        self.assertTrue(self.env['res.groups'].with_user(self.admin_user).has_access('write'))
        self.assertTrue(self.env['res.groups.privilege'].with_user(self.admin_user).has_access('write'))
        self.assertTrue(self.env['res.config.settings'].with_user(self.admin_user).has_access('create'))
