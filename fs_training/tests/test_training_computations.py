from odoo import fields
from odoo.tests.common import TransactionCase


class TestTrainingComputations(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.activity_man_dual = cls.env.ref('fs_training.activity_man_dual')
        cls.activity_nav_dual = cls.env.ref('fs_training.activity_nav_dual')
        cls.discipline_man = cls.env.ref('fs_training.discipline_man')
        cls.discipline_nav = cls.env.ref('fs_training.discipline_nav')

    def _create_enrollment(self, code):
        class_type = self.env['fs.class.type'].create({
            'name': f'Computed Type {code}',
            'code': f'COMP{code}',
            'duration_value': 1,
            'requirement_ids': [(6, 0, [])],
            'hour_requirement_ids': [
                (0, 0, {
                    'activity_id': self.activity_man_dual.id,
                    'minimum_hours': 2.0,
                }),
                (0, 0, {
                    'activity_id': self.activity_nav_dual.id,
                    'minimum_hours': 2.0,
                }),
            ],
        })
        training_class = self.env['fs.training.class'].create({
            'name': f'Computed Class {code}',
            'code': f'CC{code}',
            'class_type_id': class_type.id,
            'start_date': fields.Date.today(),
        })
        student = self.env['fs.student'].create({
            'name': f'Computed Student {code}',
            'gender': 'male',
        })
        return self.env['fs.student.enrollment'].create({
            'training_class_id': training_class.id,
            'student_id': student.id,
        })

    def test_progression_recomputes_when_hour_moves_between_sections(self):
        enrollment = self._create_enrollment('EXTRA')
        required_man = enrollment.required_hour_ids.filtered(
            lambda line: line.activity_id == self.activity_man_dual
        )
        required_man.unlink()
        extra_hour = self.env['fs.enrollment.hours'].create({
            'enrollment_id': enrollment.id,
            'activity_id': self.activity_man_dual.id,
            'minimum_hours': 2.0,
            'hours_logged': 1.0,
            'is_extra': True,
        })

        self.assertEqual(enrollment.progression, 0.0)
        extra_hour.write({'is_extra': False})
        self.assertEqual(enrollment.progression, 25.0)

    def test_mission_duration_tracks_inherited_activity_and_discipline_defaults(self):
        class_type = self.env['fs.class.type'].create({
            'name': 'Duration Computed Type',
            'code': 'DURATION',
            'duration_value': 1,
            'requirement_ids': [(6, 0, [])],
        })
        mission = self.env['fs.flight.mission'].create({
            'name': 'Inherited Duration Mission',
            'class_type_id': class_type.id,
            'activity_id': self.activity_man_dual.id,
        })

        self.assertEqual(mission.duration_hours, self.discipline_man.default_flight_duration)
        self.discipline_man.write({'default_flight_duration': 1.75})
        self.assertEqual(mission.duration_hours, 1.75)

        mission.write({'activity_id': self.activity_nav_dual.id})
        self.assertEqual(mission.duration_hours, self.discipline_nav.default_flight_duration)

    def test_explicit_mission_duration_is_not_replaced_by_default_refresh(self):
        class_type = self.env['fs.class.type'].create({
            'name': 'Explicit Duration Type',
            'code': 'EXPLICITDURATION',
            'duration_value': 1,
            'requirement_ids': [(6, 0, [])],
        })
        mission = self.env['fs.flight.mission'].create({
            'name': 'Explicit Duration Mission',
            'class_type_id': class_type.id,
            'activity_id': self.activity_man_dual.id,
            'duration_hours': self.discipline_man.default_flight_duration,
        })

        self.discipline_man.write({'default_flight_duration': 2.25})
        self.assertEqual(mission.duration_hours, 1.0)
