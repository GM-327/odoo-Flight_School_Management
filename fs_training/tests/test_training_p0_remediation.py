from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestTrainingP0Remediation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.activity_man_dual = cls.env.ref('fs_training.activity_man_dual')

    def _create_class_type(self, code, **values):
        class_type_values = {
            'name': f'P0 Type {code}',
            'code': code,
            'duration_value': 1,
            'requirement_ids': [(6, 0, [])],
        }
        class_type_values.update(values)
        return self.env['fs.class.type'].create(class_type_values)

    def _create_class(self, class_type, code):
        return self.env['fs.training.class'].create({
            'name': f'P0 Class {code}',
            'code': f'P0{code}',
            'class_type_id': class_type.id,
            'start_date': fields.Date.today(),
        })

    def _create_student(self, code, **values):
        student_values = {'name': f'P0 Student {code}', 'gender': 'male'}
        student_values.update(values)
        return self.env['fs.student'].create(student_values)

    def _create_enrollment(self, training_class, student):
        return self.env['fs.student.enrollment'].create({
            'training_class_id': training_class.id,
            'student_id': student.id,
        })

    def test_create_replaces_forged_requirement_snapshots(self):
        class_type = self._create_class_type('SNAP', hour_requirement_ids=[(0, 0, {
            'activity_id': self.activity_man_dual.id,
            'minimum_hours': 2.0,
        })])
        training_class = self._create_class(class_type, 'SNAP')
        student = self._create_student('SNAP')

        enrollment = self.env['fs.student.enrollment'].create({
            'training_class_id': training_class.id,
            'student_id': student.id,
            'required_hour_ids': [(0, 0, {
                'activity_id': self.activity_man_dual.id,
                'minimum_hours': 999.0,
            })],
        })

        self.assertEqual(enrollment.required_hour_ids.minimum_hours, 2.0)
        with self.assertRaises(ValidationError):
            enrollment.write({'required_hour_ids': [(5, 0, 0)]})
        with self.assertRaises(ValidationError):
            enrollment.required_hour_ids.write({'minimum_hours': 999.0})
        other_class = self._create_class(class_type, 'SNAPOTHER')
        with self.assertRaises(ValidationError):
            enrollment.training_class_id = other_class

    def test_class_start_enforces_configured_medical_and_military_requirements(self):
        medical_requirement = self.env['fs.class.requirement'].create({
            'name': 'P0 Medical',
            'category': 'medical',
            'is_military': True,
            'is_civilian': True,
        })
        class_type = self._create_class_type(
            'ELIG', requirement_ids=[(6, 0, [medical_requirement.id])],
        )
        training_class = self._create_class(class_type, 'ELIG')
        student = self._create_student('ELIG')
        self._create_enrollment(training_class, student)

        with self.assertRaises(ValidationError):
            training_class.action_start_class()

        student.medical_expiry = fields.Date.today() + timedelta(days=90)
        training_class.action_start_class()
        self.assertEqual(training_class.status, 'in_progress')

        military_type = self._create_class_type('MIL', is_military=True)
        military_class = self._create_class(military_type, 'MIL')
        civilian_student = self._create_student('MIL', is_military=False)
        self._create_enrollment(military_class, civilian_student)
        with self.assertRaises(ValidationError):
            military_class.action_start_class()

    def test_direct_lifecycle_writes_are_rejected_and_terminal_classes_stay_terminal(self):
        class_type = self._create_class_type('LIFE')
        training_class = self._create_class(class_type, 'LIFE')
        enrollment = self._create_enrollment(training_class, self._create_student('LIFE'))

        with self.assertRaises(ValidationError):
            training_class.write({'status': 'in_progress'})
        with self.assertRaises(ValidationError):
            enrollment.write({'status': 'active'})

        training_class.action_start_class()
        training_class.actual_end_date = fields.Date.today()
        training_class.action_complete_class()
        self.assertEqual(training_class.status, 'completed')
        with self.assertRaises(ValidationError):
            training_class.action_set_draft()

    def test_class_archive_does_not_archive_students(self):
        class_type = self._create_class_type('ARCH')
        training_class = self._create_class(class_type, 'ARCH')
        student = self._create_student('ARCH')
        self._create_enrollment(training_class, student)

        training_class.active = False

        self.assertFalse(training_class.active)
        self.assertTrue(student.active)

    def test_extra_hour_posting_remains_available_to_flight_integrations(self):
        class_type = self._create_class_type('HOURS')
        training_class = self._create_class(class_type, 'HOURS')
        enrollment = self._create_enrollment(training_class, self._create_student('HOURS'))

        extra_hour = self.env['fs.enrollment.hours'].create({
            'enrollment_id': enrollment.id,
            'activity_id': self.activity_man_dual.id,
            'hours_logged': 1.0,
            'is_extra': True,
        })
        extra_hour.sudo().write({'hours_logged': 2.5})

        self.assertEqual(extra_hour.hours_logged, 2.5)

    def test_graduation_requires_all_mandatory_missions(self):
        class_type = self._create_class_type('MISSION')
        mission = self.env['fs.flight.mission'].create({
            'name': 'P0 Mandatory Mission',
            'class_type_id': class_type.id,
            'activity_id': self.activity_man_dual.id,
            'sequence': 10,
        })
        training_class = self._create_class(class_type, 'MISSION')
        enrollment = self._create_enrollment(training_class, self._create_student('MISSION'))
        training_class.action_start_class()

        with self.assertRaises(UserError):
            enrollment.action_graduate()
        training_class.actual_end_date = fields.Date.today()
        with self.assertRaises(UserError):
            training_class.action_complete_class()

        completion = self.env['fs.mission.completion'].create({
            'enrollment_id': enrollment.id,
            'mission_id': mission.id,
        })
        completion.action_mark_complete()
        training_class.action_complete_class()
        self.assertEqual(training_class.status, 'completed')
        self.assertEqual(enrollment.status, 'graduated')
