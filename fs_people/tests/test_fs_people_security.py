import importlib.util
from pathlib import Path

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


MIGRATION_PATH = Path(__file__).parents[1] / 'migrations' / '19.0.1.0.1' / 'post-migration.py'
MIGRATION_SPEC = importlib.util.spec_from_file_location('fs_people_fixture_cleanup', MIGRATION_PATH)
MIGRATION_MODULE = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(MIGRATION_MODULE)


class TestFsPeopleSecurity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        instructor_group = cls.env.ref('fs_core.group_flight_school_instructor')
        cls.instructor_user = cls.env['res.users'].create({
            'name': 'People Instructor User',
            'login': 'people.instructor@example.com',
            'group_ids': [(6, 0, [instructor_group.id])],
        })

    def test_instructor_cannot_write_personnel_records(self):
        instructor = self.env['fs.instructor'].create({
            'name': 'Instructor Access Test',
            'gender': 'female',
        })
        student = self.env['fs.student'].create({
            'name': 'Student Access Test',
            'gender': 'male',
        })

        self.assertFalse(self.env['fs.instructor'].with_user(self.instructor_user).has_access('write'))
        self.assertFalse(self.env['fs.student'].with_user(self.instructor_user).has_access('write'))
        with self.assertRaises(AccessError):
            instructor.with_user(self.instructor_user).write({'phone': '555-0100'})
        with self.assertRaises(AccessError):
            student.with_user(self.instructor_user).write({'medical_expiry': '2030-01-01'})

    def test_qualification_badges_escape_editable_labels(self):
        qualification = self.env['fs.qualification.type'].create({
            'name': 'Unsafe qualification name',
            'code': '<img src=x onerror=alert(1)>',
        })
        instructor = self.env['fs.instructor'].create({
            'name': 'Instructor Badge Test',
            'gender': 'female',
        })
        pilot = self.env['fs.pilot'].create({
            'name': 'Pilot Badge Test',
            'gender': 'male',
        })
        self.env['fs.person.qualification'].create({
            'instructor_id': instructor.id,
            'qualification_id': qualification.id,
        })
        self.env['fs.person.qualification'].create({
            'pilot_id': pilot.id,
            'qualification_id': qualification.id,
        })

        for badge_html in (instructor.qualification_badges, pilot.qualification_badges):
            self.assertIn('&lt;img', badge_html)
            self.assertNotIn('<img', badge_html)

    def test_fixture_cleanup_migration_deletes_only_unreferenced_xmlid_records(self):
        qualification_type = self.env['fs.qualification.type'].create({
            'name': 'Migration Qualification',
            'code': 'MIGRATION',
        })
        removable_instructor = self.env['fs.instructor'].create({
            'name': 'Removable Legacy Instructor',
            'gender': 'male',
        })
        referenced_instructor = self.env['fs.instructor'].create({
            'name': 'Referenced Legacy Instructor',
            'gender': 'female',
        })
        removable_pilot = self.env['fs.pilot'].create({
            'name': 'Removable Legacy Pilot',
            'gender': 'male',
        })
        removable_qualification = self.env['fs.person.qualification'].create({
            'instructor_id': removable_instructor.id,
            'qualification_id': qualification_type.id,
        })
        user_qualification = self.env['fs.person.qualification'].create({
            'instructor_id': referenced_instructor.id,
            'qualification_id': qualification_type.id,
        })
        self.env['ir.model.data'].create([
            {
                'module': 'fs_people',
                'name': 'instructor_youssef_khelifa',
                'model': 'fs.instructor',
                'res_id': removable_instructor.id,
                'noupdate': True,
            },
            {
                'module': 'fs_people',
                'name': 'instructor_anis_gharsallah',
                'model': 'fs.instructor',
                'res_id': referenced_instructor.id,
                'noupdate': True,
            },
            {
                'module': 'fs_people',
                'name': 'pilot_souheil_matoussi',
                'model': 'fs.pilot',
                'res_id': removable_pilot.id,
                'noupdate': True,
            },
            {
                'module': 'fs_people',
                'name': 'person_qualification_3_single_engine_piston',
                'model': 'fs.person.qualification',
                'res_id': removable_qualification.id,
                'noupdate': True,
            },
        ])

        MIGRATION_MODULE.migrate(self.env.cr, '19.0.1.0.0')

        self.assertFalse(removable_qualification.exists())
        self.assertFalse(removable_pilot.exists())
        self.assertFalse(removable_instructor.exists())
        self.assertTrue(user_qualification.exists())
        self.assertTrue(referenced_instructor.exists())
        remaining_legacy_data = self.env['ir.model.data'].search([
            ('module', '=', 'fs_people'),
            ('name', 'in', [
                'instructor_youssef_khelifa',
                'instructor_anis_gharsallah',
                'pilot_souheil_matoussi',
                'person_qualification_3_single_engine_piston',
            ]),
        ])
        self.assertEqual(
            remaining_legacy_data.res_id,
            referenced_instructor.id,
        )
