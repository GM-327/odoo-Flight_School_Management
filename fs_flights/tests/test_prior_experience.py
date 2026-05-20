from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestPriorExperience(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.activity_man_dual = cls.env.ref('fs_training.activity_man_dual')
        cls.group_user = cls.env.ref('fs_core.group_flight_school_user')
        cls.group_manager = cls.env.ref('fs_core.group_flight_school_manager')
        cls.basic_user = cls.env['res.users'].create({
            'name': 'Prior Experience User',
            'login': 'prior.experience.user@example.com',
            'group_ids': [(6, 0, [cls.group_user.id])],
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Prior Experience Manager',
            'login': 'prior.experience.manager@example.com',
            'group_ids': [(6, 0, [cls.group_manager.id])],
        })

    def _create_enrollment(self, code):
        class_type = self.env['fs.class.type'].create({
            'name': f'Prior Experience Type {code}',
            'code': code,
            'duration_value': 1,
            'hour_requirement_ids': [(0, 0, {
                'activity_id': self.activity_man_dual.id,
                'minimum_hours': 5.0,
            })],
        })
        mission = self.env['fs.flight.mission'].create({
            'name': f'Prior Mission {code}',
            'class_type_id': class_type.id,
            'activity_id': self.activity_man_dual.id,
            'sequence': 1,
        })
        training_class = self.env['fs.training.class'].create({
            'name': f'Prior Training {code}',
            'code': f'T{code}',
            'class_type_id': class_type.id,
            'start_date': fields.Date.today(),
        })
        student = self.env['fs.student'].create({
            'name': f'Prior Student {code}',
            'gender': 'male',
        })
        enrollment = self.env['fs.student.enrollment'].create({
            'student_id': student.id,
            'training_class_id': training_class.id,
        })
        return student, enrollment, mission

    def _approve_and_apply(self, experience):
        experience.with_user(self.manager_user).action_submit_for_review()
        experience.with_user(self.manager_user).action_approve()
        experience.with_user(self.manager_user).action_apply_hours()

    def test_prior_hours_apply_revert_and_reapply(self):
        student, enrollment, _mission = self._create_enrollment('PRIORHRS')
        experience = self.env['fs.initial.experience'].create({
            'person_type': 'student',
            'student_id': student.id,
            'source_type': 'previous_school',
            'source_organization': 'Legacy Flight School',
            'line_ids': [
                (0, 0, {
                    'hour_kind': 'flight',
                    'hours': 2.0,
                    'enrollment_id': enrollment.id,
                    'activity_id': self.activity_man_dual.id,
                    'count_toward_enrollment': True,
                }),
                (0, 0, {
                    'hour_kind': 'simulator',
                    'hours': 1.5,
                    'enrollment_id': enrollment.id,
                    'activity_id': self.activity_man_dual.id,
                    'count_toward_enrollment': True,
                }),
            ],
        })

        self._approve_and_apply(experience)
        requirement_line = enrollment.required_hour_ids.filtered(
            lambda line: line.activity_id == self.activity_man_dual
        )

        self.assertEqual(experience.state, 'applied')
        self.assertTrue(experience.is_applied)
        self.assertEqual(student.total_flight_hours, 2.0)
        self.assertEqual(student.total_sim_hours, 1.5)
        self.assertEqual(requirement_line.hours_logged, 3.5)

        experience.with_user(self.manager_user).action_apply_hours()
        self.assertEqual(student.total_flight_hours, 2.0)
        self.assertEqual(requirement_line.hours_logged, 3.5)

        experience.with_user(self.manager_user).action_revert_hours()
        self.assertEqual(experience.state, 'approved')
        self.assertFalse(experience.is_applied)
        self.assertEqual(student.total_flight_hours, 0.0)
        self.assertEqual(student.total_sim_hours, 0.0)
        self.assertEqual(requirement_line.hours_logged, 0.0)

        experience.with_user(self.manager_user).action_apply_hours()
        self.assertEqual(student.total_flight_hours, 2.0)
        self.assertEqual(student.total_sim_hours, 1.5)
        self.assertEqual(requirement_line.hours_logged, 3.5)

    def test_prior_syllabus_completion_updates_and_restores_existing_completion(self):
        student, enrollment, mission = self._create_enrollment('PRIORMIS')
        existing_completion = self.env['fs.mission.completion'].create({
            'enrollment_id': enrollment.id,
            'mission_id': mission.id,
            'is_completed': False,
            'source': 'manual',
            'source_reference': 'manual-before-prior',
        })
        experience = self.env['fs.initial.experience'].create({
            'person_type': 'student',
            'student_id': student.id,
            'source_type': 'previous_school',
            'source_organization': 'Legacy Academy',
            'source_reference': 'LOG-42',
            'syllabus_completion_ids': [(0, 0, {
                'enrollment_id': enrollment.id,
                'mission_id': mission.id,
                'completion_date': fields.Date.today(),
                'notes': 'Completed before onboarding.',
            })],
        })

        self._approve_and_apply(experience)
        prior_line = experience.syllabus_completion_ids

        self.assertEqual(prior_line.generated_completion_id, existing_completion)
        self.assertTrue(existing_completion.is_completed)
        self.assertEqual(existing_completion.source, 'prior_experience')
        self.assertTrue(existing_completion.is_prior_experience)
        self.assertEqual(existing_completion.source_record_model, 'fs.prior.syllabus.completion')
        self.assertEqual(existing_completion.source_record_id, prior_line.id)

        experience.with_user(self.manager_user).action_revert_hours()
        self.assertTrue(existing_completion.exists())
        self.assertFalse(existing_completion.is_completed)
        self.assertEqual(existing_completion.source, 'manual')
        self.assertEqual(existing_completion.source_reference, 'manual-before-prior')
        self.assertFalse(existing_completion.is_prior_experience)

    def test_prior_experience_validates_person_hours_and_manager_workflow(self):
        student, _enrollment, _mission = self._create_enrollment('PRIORSEC')

        with self.assertRaises(ValidationError):
            self.env['fs.initial.experience'].create({
                'person_type': 'student',
                'student_id': student.id,
                'initial_flight_hours': -1.0,
            })

        with self.assertRaises(AccessError):
            self.env['fs.initial.experience'].with_user(self.basic_user).create({
                'person_type': 'student',
                'student_id': student.id,
            })

        experience = self.env['fs.initial.experience'].create({
            'person_type': 'student',
            'student_id': student.id,
            'initial_flight_hours': 1.0,
        })
        experience.with_user(self.manager_user).action_submit_for_review()
        experience.with_user(self.manager_user).action_approve()

        with self.assertRaises(AccessError):
            experience.with_user(self.basic_user).action_apply_hours()

        experience.with_user(self.manager_user).action_apply_hours()
        self.assertEqual(student.total_flight_hours, 1.0)
        self.assertEqual(experience.state, 'applied')
