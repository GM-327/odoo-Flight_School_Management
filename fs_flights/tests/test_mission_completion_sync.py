from datetime import date, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestOperationalMissionCompletionSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.activity = cls.env.ref('fs_training.activity_man_dual')
        cls.category = cls.env['fs.aircraft.category'].create({
            'name': 'Completion Test Category',
            'code': 'CTC',
        })
        cls.aircraft_type = cls.env['fs.aircraft.type'].create({
            'name': 'Completion Test Aircraft',
            'manufacturer': 'Completion Test Manufacturer',
            'category_id': cls.category.id,
        })

    def _create_training_context(self, code):
        class_type = self.env['fs.class.type'].create({
            'name': f'Completion Type {code}',
            'code': code,
            'duration_value': 1,
            'requirement_ids': [(6, 0, [])],
        })
        mission = self.env['fs.flight.mission'].create({
            'name': f'Completion Mission {code}',
            'class_type_id': class_type.id,
            'activity_id': self.activity.id,
            'sequence': 10,
        })
        training_class = self.env['fs.training.class'].create({
            'name': f'Completion Class {code}',
            'code': f'CM{code}',
            'class_type_id': class_type.id,
            'start_date': fields.Date.today(),
        })
        student = self.env['fs.student'].create({
            'name': f'Completion Student {code}',
            'gender': 'male',
        })
        enrollment = self.env['fs.student.enrollment'].create({
            'student_id': student.id,
            'training_class_id': training_class.id,
        })
        training_class.action_start_class()
        crew = self.env['fs.crew.member'].search([
            ('enrollment_id', '=', enrollment.id),
        ], limit=1)
        self.assertTrue(crew)
        return enrollment, mission, crew

    def _create_flight(self, callsign, mission, crew):
        aircraft = self.env['fs.aircraft'].create({
            'registration': f'TS-{callsign}',
            'aircraft_type_id': self.aircraft_type.id,
        })
        return self.env['fs.flight'].create({
            'callsign': callsign,
            'date': date.today(),
            'scheduled_start': 8.0,
            'scheduled_duration': 1.0,
            'flight_category': 'student_training',
            'aircraft_id': aircraft.id,
            'pilot1_crew_id': crew.id,
            'pilot1_function': 'student',
            'mission_id': mission.id,
        })

    def _complete(self, flight):
        flight.write({'atd': 9.0, 'ata': 10.0, 'status': 'done'})

    def _completion(self, enrollment, mission):
        return self.env['fs.mission.completion'].search([
            ('enrollment_id', '=', enrollment.id),
            ('mission_id', '=', mission.id),
        ])

    def test_completed_flight_creates_updates_and_reverses_completion(self):
        enrollment, mission, crew = self._create_training_context('OPCREATE')
        flight = self._create_flight('OP1001', mission, crew)

        self._complete(flight)
        completion = self._completion(enrollment, mission)
        self.assertTrue(completion.is_completed)
        self.assertEqual(completion.source, 'operational_flight')
        self.assertEqual(completion.source_record_id, flight.id)
        self.assertFalse(enrollment._get_incomplete_mandatory_missions())

        corrected_date = date.today() + timedelta(days=1)
        flight.write({'callsign': 'OP1001C', 'date': corrected_date, 'notes': 'Corrected log'})
        self.assertEqual(completion.source_reference, 'OP1001C')
        self.assertEqual(completion.completion_date, corrected_date)
        self.assertEqual(completion.source_notes, 'Corrected log')

        flight.write({'status': 'cancelled'})
        self.assertFalse(completion.exists())
        self.assertTrue(enrollment._get_incomplete_mandatory_missions())
        flight.unlink()

    def test_operational_reversal_restores_manual_and_prior_sources(self):
        enrollment, mission, crew = self._create_training_context('OPSOURCE')
        completion = self.env['fs.mission.completion'].create({
            'enrollment_id': enrollment.id,
            'mission_id': mission.id,
            'is_completed': False,
            'source': 'manual',
            'source_reference': 'MANUAL-REFERENCE',
        })
        flight = self._create_flight('OP1002', mission, crew)

        self._complete(flight)
        self.assertEqual(completion.source, 'operational_flight')
        flight.write({'status': 'cancelled'})
        self.assertFalse(completion.is_completed)
        self.assertEqual(completion.source, 'manual')
        self.assertEqual(completion.source_reference, 'MANUAL-REFERENCE')

        completion.write({
            'is_completed': True,
            'source': 'prior_experience',
            'source_reference': 'PRIOR-REFERENCE',
            'is_prior_experience': True,
            'source_record_model': 'fs.prior.syllabus.completion',
            'source_record_id': 123,
        })
        self._complete(flight)
        self.assertEqual(completion.source, 'operational_flight')
        flight.write({'status': 'cancelled'})
        self.assertTrue(completion.is_completed)
        self.assertEqual(completion.source, 'prior_experience')
        self.assertEqual(completion.source_reference, 'PRIOR-REFERENCE')
        self.assertTrue(completion.is_prior_experience)

    def test_repeated_completed_mission_transfers_ownership_before_reversal(self):
        enrollment, mission, crew = self._create_training_context('OPRETRY')
        first_flight = self._create_flight('OP1003', mission, crew)
        second_flight = self._create_flight('OP1004', mission, crew)

        self._complete(first_flight)
        self._complete(second_flight)
        completion = self._completion(enrollment, mission)
        self.assertEqual(completion.source_record_id, first_flight.id)
        self.assertEqual(len(completion), 1)

        first_flight.write({'status': 'cancelled'})
        self.assertEqual(completion.source, 'operational_flight')
        self.assertEqual(completion.source_record_id, second_flight.id)

        second_flight.write({'status': 'cancelled'})
        self.assertFalse(completion.exists())

    def test_reversal_after_graduation_restores_source_and_hours(self):
        enrollment, mission, crew = self._create_training_context('OPGRAD')
        completion = self.env['fs.mission.completion'].create({
            'enrollment_id': enrollment.id,
            'mission_id': mission.id,
            'is_completed': False,
            'source': 'manual',
            'source_reference': 'MANUAL-BEFORE-GRADUATION',
        })
        flight = self._create_flight('OP1005', mission, crew)

        self._complete(flight)
        self.assertEqual(enrollment.total_hours, 1.0)
        enrollment.training_class_id.actual_end_date = date.today()
        enrollment.training_class_id.action_complete_class()
        self.assertEqual(enrollment.status, 'graduated')

        flight.write({'status': 'cancelled'})
        self.assertTrue(completion.exists())
        self.assertFalse(completion.is_completed)
        self.assertEqual(completion.source, 'manual')
        self.assertEqual(completion.source_reference, 'MANUAL-BEFORE-GRADUATION')
        self.assertEqual(enrollment.total_hours, 0.0)

    def test_reversal_after_drop_removes_completion_and_hours(self):
        enrollment, mission, crew = self._create_training_context('OPDROP')
        flight = self._create_flight('OP1006', mission, crew)

        self._complete(flight)
        completion = self._completion(enrollment, mission)
        self.assertEqual(enrollment.total_hours, 1.0)
        enrollment.action_drop()
        self.assertEqual(enrollment.status, 'dropped')

        flight.write({'status': 'cancelled'})
        self.assertFalse(completion.exists())
        self.assertEqual(enrollment.total_hours, 0.0)
