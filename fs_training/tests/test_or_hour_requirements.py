from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestOrHourRequirements(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.activity_man_dual = cls.env.ref('fs_training.activity_man_dual')
        cls.activity_nav_dual = cls.env.ref('fs_training.activity_nav_dual')
        cls.activity_vsv_sim = cls.env.ref('fs_training.activity_vsv_sim')
        cls.activity_ifr_dual = cls.env.ref('fs_training.activity_ifr_dual')

    def _create_or_class_type(self, code='ORREQ'):
        return self.env['fs.class.type'].create({
            'name': f'OR Requirement Type {code}',
            'code': code,
            'duration_value': 1,
            'hour_requirement_ids': [(0, 0, {
                'activity_id': self.activity_man_dual.id,
                'minimum_hours': 2.0,
            })],
            'hour_requirement_group_ids': [(0, 0, {
                'name': 'Instrument Alternatives',
                'minimum_hours': 5.0,
                'count_as': 'simulator',
                'hour_requirement_ids': [
                    (0, 0, {'activity_id': self.activity_vsv_sim.id}),
                    (0, 0, {'activity_id': self.activity_ifr_dual.id}),
                ],
            })],
        })

    def _create_enrollment(self, class_type):
        training_class = self.env['fs.training.class'].create({
            'name': f'Training {class_type.code}',
            'code': f'T{class_type.code}',
            'class_type_id': class_type.id,
            'start_date': fields.Date.today(),
        })
        student = self.env['fs.student'].create({
            'name': f'Student {class_type.code}',
            'gender': 'male',
        })
        return self.env['fs.student.enrollment'].create({
            'student_id': student.id,
            'training_class_id': training_class.id,
        })

    def test_or_group_totals_use_count_as_once(self):
        class_type = self._create_or_class_type('ORREQ1')

        self.assertEqual(class_type.total_required_hours, 7.0)
        self.assertEqual(class_type.total_required_aircraft_hours, 2.0)
        self.assertEqual(class_type.total_required_simulator_hours, 5.0)

    def test_same_activity_can_be_used_in_multiple_or_groups(self):
        class_type = self._create_or_class_type('ORREQ2')

        class_type.write({
            'hour_requirement_group_ids': [(0, 0, {
                'name': 'Second Alternatives',
                'minimum_hours': 3.0,
                'count_as': 'aircraft',
                'hour_requirement_ids': [
                    (0, 0, {'activity_id': self.activity_vsv_sim.id}),
                    (0, 0, {'activity_id': self.activity_nav_dual.id}),
                ],
            })],
        })

        self.assertEqual(len(class_type.hour_requirement_group_ids), 2)
        self.assertEqual(class_type.total_required_hours, 10.0)
        self.assertEqual(class_type.total_required_aircraft_hours, 5.0)
        self.assertEqual(class_type.total_required_simulator_hours, 5.0)

    def test_duplicate_activity_in_same_or_group_is_rejected(self):
        class_type = self._create_or_class_type('ORREQ3')

        with self.assertRaises(ValidationError):
            self.env['fs.class.type.hours.group'].create({
                'class_type_id': class_type.id,
                'name': 'Invalid Alternatives',
                'minimum_hours': 1.0,
                'count_as': 'aircraft',
                'hour_requirement_ids': [
                    (0, 0, {'activity_id': self.activity_nav_dual.id}),
                    (0, 0, {'activity_id': self.activity_nav_dual.id}),
                ],
            })

    def test_enrollment_or_group_uses_snapshot_and_matching_extra_hours(self):
        class_type = self._create_or_class_type('ORREQ4')
        enrollment = self._create_enrollment(class_type)

        self.assertEqual(len(enrollment.requirement_group_ids), 1)
        self.assertEqual(enrollment.remaining_hours, 7.0)

        vsv_line = enrollment.required_hour_ids.filtered(
            lambda line: line.activity_id == self.activity_vsv_sim
        )
        vsv_line.hours_logged = 2.0
        self.env['fs.enrollment.hours'].create({
            'enrollment_id': enrollment.id,
            'activity_id': self.activity_ifr_dual.id,
            'hours_logged': 3.0,
            'is_extra': True,
        })

        self.assertEqual(enrollment.requirement_group_ids.logged_hours, 5.0)
        self.assertEqual(enrollment.requirement_group_ids.remaining_hours, 0.0)
        self.assertEqual(enrollment.remaining_hours, 2.0)

        source_group = class_type.hour_requirement_group_ids
        source_group.minimum_hours = 10.0
        self.assertEqual(enrollment.requirement_group_ids.minimum_hours, 5.0)

        man_line = enrollment.required_hour_ids.filtered(
            lambda line: line.activity_id == self.activity_man_dual
        )
        man_line.hours_logged = 2.0
        self.assertEqual(enrollment.progression, 100.0)
