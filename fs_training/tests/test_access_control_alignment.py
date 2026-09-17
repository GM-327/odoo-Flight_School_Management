from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestTrainingAccessControlAlignment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.activity = cls.env.ref('fs_training.activity_man_dual')
        user_group = cls.env.ref('fs_core.group_flight_school_user')
        instructor_group = cls.env.ref('fs_core.group_flight_school_instructor')
        manager_group = cls.env.ref('fs_core.group_flight_school_manager')
        admin_group = cls.env.ref('fs_core.group_flight_school_admin')
        cls.basic_user = cls.env['res.users'].create({
            'name': 'Training Read-Only User',
            'login': 'training.readonly@example.com',
            'group_ids': [(6, 0, [user_group.id])],
        })
        cls.instructor_user = cls.env['res.users'].create({
            'name': 'Assigned Progress Instructor',
            'login': 'training.instructor@example.com',
            'group_ids': [(6, 0, [instructor_group.id])],
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Training Operations Manager',
            'login': 'training.manager@example.com',
            'group_ids': [(6, 0, [manager_group.id])],
        })
        cls.admin_user = cls.env['res.users'].create({
            'name': 'Training Configuration Administrator',
            'login': 'training.admin@example.com',
            'group_ids': [(6, 0, [admin_group.id])],
        })
        cls.assigned_instructor = cls.env['fs.instructor'].create({
            'name': 'Assigned Progress Instructor',
            'gender': 'female',
            'user_id': cls.instructor_user.id,
        })
        cls.other_instructor = cls.env['fs.instructor'].create({
            'name': 'Other Progress Instructor',
            'gender': 'male',
        })
        cls.class_type = cls.env['fs.class.type'].create({
            'name': 'Access Control Class Type',
            'code': 'ACCTL',
            'duration_value': 1,
            'requirement_ids': [(6, 0, [])],
        })
        cls.mission = cls.env['fs.flight.mission'].create({
            'name': 'Access Control Mission',
            'class_type_id': cls.class_type.id,
            'activity_id': cls.activity.id,
            'sequence': 10,
        })
        cls.training_class = cls.env['fs.training.class'].create({
            'name': 'Access Control Class',
            'code': 'ACCTL',
            'class_type_id': cls.class_type.id,
            'start_date': fields.Date.today(),
        })
        cls.assigned_enrollment = cls.env['fs.student.enrollment'].create({
            'student_id': cls.env['fs.student'].create({
                'name': 'Assigned Progress Student',
                'gender': 'female',
            }).id,
            'training_class_id': cls.training_class.id,
            'instructor_id': cls.assigned_instructor.id,
        })
        cls.other_enrollment = cls.env['fs.student.enrollment'].create({
            'student_id': cls.env['fs.student'].create({
                'name': 'Unassigned Progress Student',
                'gender': 'male',
            }).id,
            'training_class_id': cls.training_class.id,
            'instructor_id': cls.other_instructor.id,
        })
        cls.assigned_completion = cls.env['fs.mission.completion'].create({
            'enrollment_id': cls.assigned_enrollment.id,
            'mission_id': cls.mission.id,
        })
        cls.other_completion = cls.env['fs.mission.completion'].create({
            'enrollment_id': cls.other_enrollment.id,
            'mission_id': cls.mission.id,
        })

    def test_base_users_and_instructors_cannot_write_enrollments_or_admin_tasks(self):
        self.assertFalse(
            self.env['fs.student.enrollment'].with_user(self.instructor_user).has_access('write')
        )
        self.assertFalse(self.env['fs.admin.task'].with_user(self.basic_user).has_access('write'))
        self.assertFalse(self.env['fs.training.dashboard'].with_user(self.basic_user).has_access('create'))
        self.assertTrue(self.env['fs.training.dashboard'].with_user(self.manager_user).has_access('create'))
        with self.assertRaises(AccessError):
            self.assigned_enrollment.with_user(self.instructor_user).write({'notes': 'Forbidden'})

    def test_instructors_only_update_manual_progress_for_assigned_enrollments(self):
        completion = self.assigned_completion.with_user(self.instructor_user)

        self.assertFalse(self.env['fs.mission.completion'].with_user(self.basic_user).has_access('write'))
        self.assertTrue(completion.has_access('write'))
        self.assertFalse(completion.has_access('create'))
        completion.write({
            'is_completed': True,
            'completion_date': fields.Date.today(),
            'notes': 'Observed and completed.',
        })
        self.assertTrue(self.assigned_completion.is_completed)

        self.assertFalse(self.env['fs.mission.completion'].with_user(self.instructor_user).search([
            ('id', '=', self.other_completion.id),
        ]))
        with self.assertRaises(AccessError):
            self.other_completion.with_user(self.instructor_user).write({'is_completed': True})
        with self.assertRaises(AccessError):
            completion.write({'source': 'operational_flight'})

    def test_instructors_cannot_alter_system_recorded_completions(self):
        self.assigned_completion.with_user(self.manager_user).write({
            'source': 'operational_flight',
        })

        with self.assertRaises(AccessError):
            self.assigned_completion.with_user(self.instructor_user).write({
                'is_completed': True,
            })

    def test_managers_retain_all_mission_completion_access(self):
        self.other_completion.with_user(self.manager_user).write({
            'is_completed': True,
            'completion_date': fields.Date.today(),
            'source': 'manual',
        })
        self.assertTrue(self.other_completion.is_completed)

    def test_only_administrators_manage_mission_configuration(self):
        mission_model = self.env['fs.flight.mission']

        self.assertFalse(mission_model.with_user(self.manager_user).has_access('create'))
        self.assertTrue(mission_model.with_user(self.admin_user).has_access('create'))
