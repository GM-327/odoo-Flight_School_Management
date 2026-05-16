import base64
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestFsDocuments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.student = cls.env['fs.student'].create({
            'name': 'Document Test Student',
            'gender': 'male',
        })
        cls.class_type = cls.env['fs.class.type'].create({
            'name': 'Document Test Class Type',
            'code': 'DOC-TST',
        })
        cls.training_class = cls.env['fs.training.class'].create({
            'name': 'Document Test Class',
            'code': 'DOCTST26',
            'class_type_id': cls.class_type.id,
            'start_date': fields.Date.today(),
        })
        cls.admin_task = cls.env['fs.admin.task'].create({
            'name': 'Archive Signed Form',
            'training_class_id': cls.training_class.id,
        })
        cls.medical_type = cls.env.ref('fs_documents.document_type_medical')
        cls.license_type = cls.env.ref('fs_documents.document_type_license')
        cls.admin_type = cls.env.ref('fs_documents.document_type_admin')
        cls.ip_type = cls.env.ref('fs_documents.document_type_IP')
        cls.file_data = base64.b64encode(b'test document')

    def _create_student_document(self, document_type=None):
        return self.env['fs.document'].create({
            'document_type_id': (document_type or self.medical_type).id,
            'student_id': self.student.id,
        })

    def test_document_type_must_apply_to_entity(self):
        with self.assertRaises(ValidationError):
            self._create_student_document(self.license_type)

    def test_current_version_requires_expiry_when_type_has_expiry(self):
        document = self._create_student_document()
        with self.assertRaises(ValidationError):
            self.env['fs.document.version'].create({
                'document_id': document.id,
                'file': self.file_data,
                'filename': 'medical.pdf',
            })

    def test_version_numbers_and_current_version_progress(self):
        document = self._create_student_document()
        version_1 = self.env['fs.document.version'].create({
            'document_id': document.id,
            'file': self.file_data,
            'filename': 'medical-v1.pdf',
            'expiry_date': fields.Date.today() + timedelta(days=30),
        })
        version_2 = self.env['fs.document.version'].create({
            'document_id': document.id,
            'file': self.file_data,
            'filename': 'medical-v2.pdf',
            'expiry_date': fields.Date.today() + timedelta(days=60),
        })

        self.assertEqual(version_1.version_number, 1)
        self.assertEqual(version_2.version_number, 2)
        self.assertFalse(version_1.is_current)
        self.assertTrue(version_2.is_current)
        self.assertEqual(document.current_version_id, version_2)

    def test_admin_documents_are_archived_per_admin_task(self):
        document = self.env['fs.document'].create({
            'document_type_id': self.admin_type.id,
            'admin_task_id': self.admin_task.id,
        })
        self.env['fs.document.version'].create({
            'document_id': document.id,
            'file': self.file_data,
            'filename': 'signed-form.pdf',
        })

        self.assertEqual(document.related_entity_type, 'admin_task')
        self.assertEqual(document.related_entity_name, self.admin_task.display_name)
        self.assertEqual(self.admin_task.document_count, 1)

    def test_admin_task_context_prefills_wizard(self):
        wizard = self.env['fs.document.upload.wizard'].with_context(
            default_admin_task_id=self.admin_task.id,
        ).create({})

        self.assertEqual(wizard.entity_type_code, 'admin_task')
        self.assertEqual(wizard.admin_task_id, self.admin_task)
        self.assertEqual(wizard.training_class_id, self.training_class)

    def test_ip_upload_sets_empty_class_type_reference(self):
        wizard = self.env['fs.document.upload.wizard'].create({
            'entity_type_id': self.env.ref('fs_documents.entity_type_class_type').id,
            'class_type_id': self.class_type.id,
            'document_type_id': self.ip_type.id,
            'state': 'details',
            'file': self.file_data,
            'filename': 'ip.pdf',
        })

        action = wizard.action_submit()
        document = self.env['fs.document'].browse(action['res_id'])
        self.assertEqual(self.class_type.reference_document_id, document)

    def test_invalid_warning_days_falls_back_safely(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'flight_school.medical_warning_days', 'not-an-integer')

        self.assertEqual(self.env['fs.document']._get_warning_days('medical_expiry'), 30)

    def test_document_status_uses_related_field_warning_days(self):
        self.env['ir.config_parameter'].sudo().set_param('flight_school.medical_warning_days', '7')
        document = self._create_student_document()
        self.env['fs.document.version'].create({
            'document_id': document.id,
            'file': self.file_data,
            'filename': 'medical.pdf',
            'expiry_date': fields.Date.today() + timedelta(days=8),
        })

        document._compute_expiry_status()
        self.assertEqual(document.expiry_status, 'valid')

        document.expiry_date = fields.Date.today() + timedelta(days=7)
        document._compute_expiry_status()
        self.assertEqual(document.expiry_status, 'expiring')
