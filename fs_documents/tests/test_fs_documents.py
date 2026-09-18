import base64
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
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
        cls.ip_type = cls.env.ref('fs_documents.document_type_IP')
        admin_task_entity_type = cls.env.ref('fs_documents.entity_type_admin_task')
        class_type_entity_type = cls.env.ref('fs_documents.entity_type_class_type')
        cls.admin_task_type = cls.env['fs.document.type'].create({
            'name': 'Test Admin Task Archive',
            'code': 'TST-ADMIN-ARCHIVE',
            'applies_to_ids': [(6, 0, [admin_task_entity_type.id])],
            'has_expiry': False,
        })
        cls.invalid_for_student_type = cls.env['fs.document.type'].create({
            'name': 'Test Class Type Only',
            'code': 'TST-CLASS-TYPE-ONLY',
            'applies_to_ids': [(6, 0, [class_type_entity_type.id])],
            'has_expiry': False,
        })
        cls.file_data = base64.b64encode(b'test document')

    def _create_student_document(self, document_type=None):
        return self.env['fs.document'].create({
            'document_type_id': (document_type or self.medical_type).id,
            'student_id': self.student.id,
        })

    def test_document_type_must_apply_to_entity(self):
        with self.assertRaises(ValidationError):
            self._create_student_document(self.invalid_for_student_type)

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

    def test_version_metadata_is_server_managed(self):
        document = self._create_student_document()
        before_create = fields.Datetime.now()
        version = self.env['fs.document.version'].create({
            'document_id': document.id,
            'file': self.file_data,
            'filename': 'medical.pdf',
            'expiry_date': fields.Date.today() + timedelta(days=30),
            'version_number': 99,
            'upload_date': '2000-01-01 00:00:00',
            'uploaded_by_id': self.env.ref('base.user_root').id,
            'is_current': False,
        })

        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.uploaded_by_id, self.env.user)
        self.assertGreaterEqual(version.upload_date, before_create)
        self.assertTrue(version.is_current)
        with self.assertRaises(ValidationError):
            version.write({'version_number': 2})

    def test_direct_current_clear_promotes_previous_version(self):
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

        version_2.write({'is_current': False})

        self.assertTrue(version_1.is_current)
        self.assertFalse(version_2.is_current)
        self.assertEqual(document.current_version_id, version_1)

    def test_direct_current_clear_rejects_only_version(self):
        document = self._create_student_document()
        version = self.env['fs.document.version'].create({
            'document_id': document.id,
            'file': self.file_data,
            'filename': 'medical.pdf',
            'expiry_date': fields.Date.today() + timedelta(days=30),
        })

        with self.assertRaises(ValidationError):
            version.write({'is_current': False})

        self.assertTrue(version.is_current)
        self.assertEqual(document.current_version_id, version)

    def test_direct_current_unlink_promotes_previous_version(self):
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

        version_2.unlink()

        self.assertTrue(version_1.is_current)
        self.assertEqual(document.current_version_id, version_1)

    def test_native_rules_scope_documents_and_versions_to_owner(self):
        group_user = self.env.ref('fs_core.group_flight_school_user')
        group_admin = self.env.ref('fs_core.group_flight_school_admin')
        owner_user = self.env['res.users'].create({
            'name': 'Document Owner',
            'login': 'document.owner@example.com',
            'group_ids': [(6, 0, [group_user.id])],
        })
        other_user = self.env['res.users'].create({
            'name': 'Other Document Owner',
            'login': 'other.document.owner@example.com',
            'group_ids': [(6, 0, [group_user.id])],
        })
        admin_user = self.env['res.users'].create({
            'name': 'Document Administrator',
            'login': 'document.administrator@example.com',
            'group_ids': [(6, 0, [group_admin.id])],
        })
        owner_student = self.env['fs.student'].create({
            'name': 'Owner Student',
            'gender': 'male',
            'user_id': owner_user.id,
        })
        other_student = self.env['fs.student'].create({
            'name': 'Other Owner Student',
            'gender': 'male',
            'user_id': other_user.id,
        })
        owner_document = self.env['fs.document'].create({
            'document_type_id': self.medical_type.id,
            'student_id': owner_student.id,
        })
        other_document = self.env['fs.document'].create({
            'document_type_id': self.medical_type.id,
            'student_id': other_student.id,
        })
        owner_version = self.env['fs.document.version'].create({
            'document_id': owner_document.id,
            'file': self.file_data,
            'filename': 'owner-medical.pdf',
            'expiry_date': fields.Date.today() + timedelta(days=30),
        })
        other_version = self.env['fs.document.version'].create({
            'document_id': other_document.id,
            'file': self.file_data,
            'filename': 'other-medical.pdf',
            'expiry_date': fields.Date.today() + timedelta(days=30),
        })

        visible_documents = self.env['fs.document'].with_user(owner_user).search([
            ('id', 'in', [owner_document.id, other_document.id]),
        ])
        visible_versions = self.env['fs.document.version'].with_user(owner_user).search([
            ('id', 'in', [owner_version.id, other_version.id]),
        ])
        admin_documents = self.env['fs.document'].with_user(admin_user).search([
            ('id', 'in', [owner_document.id, other_document.id]),
        ])

        self.assertEqual(visible_documents, owner_document)
        self.assertEqual(visible_versions, owner_version)
        self.assertEqual(admin_documents, owner_document | other_document)

    def test_instructor_reads_class_material_but_writes_only_assigned_documents(self):
        instructor_group = self.env.ref('fs_core.group_flight_school_instructor')
        instructor_user = self.env['res.users'].create({
            'name': 'Class Material Instructor',
            'login': 'class.material.instructor@example.com',
            'group_ids': [(6, 0, [instructor_group.id])],
        })
        instructor = self.env['fs.instructor'].create({
            'name': 'Assigned Class Material Instructor',
            'gender': 'female',
            'user_id': instructor_user.id,
        })
        assigned_student = self.env['fs.student'].create({
            'name': 'Assigned Document Student',
            'gender': 'male',
        })
        self.env['fs.student.enrollment'].create({
            'student_id': assigned_student.id,
            'training_class_id': self.training_class.id,
            'instructor_id': instructor.id,
        })
        assigned_type = self.env['fs.document.type'].create({
            'name': 'Assigned Student Material',
            'code': 'TST-ASSIGNED-STUDENT',
            'applies_to_ids': [(6, 0, [self.env.ref('fs_documents.entity_type_student').id])],
            'has_expiry': False,
        })
        class_material_type = self.env['fs.document.type'].create({
            'name': 'Class Material Access Test',
            'code': 'TST-CLASS-MATERIAL',
            'applies_to_ids': [(6, 0, [self.env.ref('fs_documents.entity_type_class_type').id])],
            'has_expiry': False,
        })
        forbidden_class_type = self.env['fs.class.type'].create({
            'name': 'Forbidden Class Material Target',
            'code': 'DOC-TST-2',
        })
        class_document = self.env['fs.document'].create({
            'document_type_id': class_material_type.id,
            'class_type_id': self.class_type.id,
        })
        class_version = self.env['fs.document.version'].create({
            'document_id': class_document.id,
            'file': self.file_data,
            'filename': 'class-material.pdf',
        })

        instructor_document_model = self.env['fs.document'].with_user(instructor_user)
        instructor_version_model = self.env['fs.document.version'].with_user(instructor_user)
        self.assertEqual(
            instructor_document_model.search([('id', '=', class_document.id)]),
            class_document,
        )
        self.assertEqual(
            instructor_version_model.search([('id', '=', class_version.id)]),
            class_version,
        )
        with self.assertRaises(AccessError):
            class_document.with_user(instructor_user).write({'notes': 'Forbidden class edit'})
        with self.assertRaises(AccessError):
            class_version.with_user(instructor_user).write({'notes': 'Forbidden version edit'})
        with self.assertRaises(AccessError):
            instructor_document_model.create({
                'document_type_id': class_material_type.id,
                'class_type_id': forbidden_class_type.id,
            })
        with self.assertRaises(AccessError):
            instructor_version_model.create({
                'document_id': class_document.id,
                'file': self.file_data,
                'filename': 'forbidden-class-material.pdf',
            })

        assigned_document = instructor_document_model.create({
            'document_type_id': assigned_type.id,
            'student_id': assigned_student.id,
        })
        assigned_document.write({'notes': 'Instructor-maintained assigned document'})
        assigned_version = instructor_version_model.create({
            'document_id': assigned_document.id,
            'file': self.file_data,
            'filename': 'assigned-student-material.pdf',
        })
        self.assertEqual(assigned_version.document_id, assigned_document)

    def test_admin_documents_are_archived_per_admin_task(self):
        document = self.env['fs.document'].create({
            'document_type_id': self.admin_task_type.id,
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

    def test_ip_document_entity_name_updates_on_class_type_rename(self):
        class_type = self.env['fs.class.type'].create({
            'name': 'Original IP Class Type',
            'code': 'IP-REN',
        })
        document = self.env['fs.document'].create({
            'document_type_id': self.ip_type.id,
            'class_type_id': class_type.id,
        })

        self.assertEqual(document.related_entity_name, class_type.display_name)

        class_type.name = 'Renamed IP Class Type'

        self.assertEqual(document.related_entity_name, class_type.display_name)

    def test_related_entity_name_updates_for_every_supported_entity(self):
        instructor = self.env['fs.instructor'].create({
            'name': 'Document Test Instructor',
            'gender': 'male',
        })
        pilot = self.env['fs.pilot'].create({
            'name': 'Document Test Pilot',
            'gender': 'male',
        })
        document_type = self.env['fs.document.type'].create({
            'name': 'All Entity Name Test',
            'code': 'TST-ALL-ENTITY-NAME',
            'has_expiry': False,
        })
        entity_documents = [
            ('student_id', self.student),
            ('instructor_id', instructor),
            ('pilot_id', pilot),
            ('training_class_id', self.training_class),
            ('admin_task_id', self.admin_task),
            ('class_type_id', self.class_type),
        ]

        for entity_field, entity in entity_documents:
            document = self.env['fs.document'].create({
                'document_type_id': document_type.id,
                entity_field: entity.id,
            })
            self.assertEqual(document.related_entity_name, entity.display_name)

            entity.name = f'Renamed {entity.name}'

            self.assertEqual(document.related_entity_name, entity.display_name)

    def test_document_counts_update_for_supported_entity_links(self):
        instructor = self.env['fs.instructor'].create({
            'name': 'Count Test Instructor',
            'gender': 'male',
        })
        pilot = self.env['fs.pilot'].create({
            'name': 'Count Test Pilot',
            'gender': 'male',
        })
        target_instructor = self.env['fs.instructor'].create({
            'name': 'Count Test Target Instructor',
            'gender': 'male',
        })
        document_type = self.env['fs.document.type'].create({
            'name': 'All Entity Count Test',
            'code': 'TST-ALL-ENTITY-COUNT',
            'has_expiry': False,
        })
        entities = [
            ('student_id', self.student),
            ('instructor_id', instructor),
            ('pilot_id', pilot),
            ('training_class_id', self.training_class),
            ('admin_task_id', self.admin_task),
            ('class_type_id', self.class_type),
        ]

        documents = self.env['fs.document']
        for entity_field, entity in entities:
            documents |= self.env['fs.document'].create({
                'document_type_id': document_type.id,
                entity_field: entity.id,
            })

        for entity_field, entity in entities:
            self.assertEqual(entity.document_count, 1)

        documents[0].write({
            'student_id': False,
            'instructor_id': target_instructor.id,
        })
        self.assertEqual(self.student.document_count, 0)
        self.assertEqual(instructor.document_count, 1)
        self.assertEqual(target_instructor.document_count, 1)

    def test_expiry_sync_clears_on_empty_current_and_entity_or_type_change(self):
        instructor = self.env['fs.instructor'].create({
            'name': 'Expiry Sync Instructor',
            'gender': 'male',
        })
        medical_sync_type = self.env['fs.document.type'].create({
            'name': 'Medical Sync Without Required Expiry',
            'code': 'TST-MEDICAL-SYNC',
            'has_expiry': False,
            'expiry_field': 'medical_expiry',
        })
        english_sync_type = self.env['fs.document.type'].create({
            'name': 'English Sync Without Required Expiry',
            'code': 'TST-ENGLISH-SYNC',
            'has_expiry': False,
            'expiry_field': 'english_expiry',
        })
        expiry_date = fields.Date.today() + timedelta(days=30)
        document = self.env['fs.document'].create({
            'document_type_id': medical_sync_type.id,
            'student_id': self.student.id,
        })
        version = self.env['fs.document.version'].create({
            'document_id': document.id,
            'file': self.file_data,
            'filename': 'expiry-sync.pdf',
            'expiry_date': expiry_date,
        })

        self.assertEqual(self.student.medical_expiry, expiry_date)

        document.write({
            'student_id': False,
            'instructor_id': instructor.id,
        })
        self.assertFalse(self.student.medical_expiry)
        self.assertEqual(instructor.medical_expiry, expiry_date)

        document.write({'document_type_id': english_sync_type.id})
        self.assertFalse(instructor.medical_expiry)
        self.assertEqual(instructor.english_expiry, expiry_date)

        version.write({'expiry_date': False})
        self.assertFalse(instructor.english_expiry)

        version.write({'expiry_date': expiry_date})
        self.assertEqual(instructor.english_expiry, expiry_date)
        version.unlink()
        self.assertFalse(instructor.english_expiry)

    def test_invalid_warning_days_falls_back_safely(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'flight_school.medical_warning_days', 'not-an-integer')

        self.assertEqual(self.env['fs.document']._get_warning_days('medical_expiry'), 35)

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
