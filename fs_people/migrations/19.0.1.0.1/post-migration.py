# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api
from psycopg2 import IntegrityError


LEGACY_XML_IDS = {
    'fs.person.qualification': (
        'person_qualification_3_single_engine_piston',
        'person_qualification_1_instrument_rating',
        'person_qualification_2_multi_engine_rating',
        'person_qualification_8_flight_examiner',
        'person_qualification_4_flight_instructor',
        'person_qualification_6_class_rating_instructor',
        'person_qualification_5_instrument_rating_instructor',
        'person_qualification_9_class_rating_examiner',
        'person_qualification_10_instrument_rating_examiner',
        'person_qualification_7_flight_instructor_examiner',
        'person_qualification_1_instrument_rating_2',
        'person_qualification_2_multi_engine_rating_2',
        'person_qualification_3_single_engine_piston_2',
        'person_qualification_8_flight_examiner_2',
        'person_qualification_4_flight_instructor_2',
        'person_qualification_6_class_rating_instructor_2',
        'person_qualification_5_instrument_rating_instructor_2',
        'person_qualification_1_instrument_rating_3',
        'person_qualification_2_multi_engine_rating_3',
        'person_qualification_3_single_engine_piston_3',
        'person_qualification_8_flight_examiner_3',
        'person_qualification_4_flight_instructor_3',
        'person_qualification_6_class_rating_instructor_3',
        'person_qualification_5_instrument_rating_instructor_3',
        'person_qualification_9_class_rating_examiner_2',
        'person_qualification_10_instrument_rating_examiner_2',
        'person_qualification_2_multi_engine_rating_4',
        'person_qualification_1_instrument_rating_4',
        'person_qualification_3_single_engine_piston_4',
        'person_qualification_4_flight_instructor_4',
        'person_qualification_1_instrument_rating_5',
        'person_qualification_2_multi_engine_rating_5',
        'person_qualification_3_single_engine_piston_5',
        'person_qualification_4_flight_instructor_5',
        'person_qualification_1_instrument_rating_6',
        'person_qualification_2_multi_engine_rating_6',
        'person_qualification_3_single_engine_piston_6',
        'person_qualification_4_flight_instructor_6',
        'person_qualification_1_instrument_rating_7',
        'person_qualification_2_multi_engine_rating_7',
        'person_qualification_3_single_engine_piston_7',
        'person_qualification_4_flight_instructor_7',
        'person_qualification_1_instrument_rating_8',
        'person_qualification_2_multi_engine_rating_8',
        'person_qualification_3_single_engine_piston_8',
        'person_qualification_4_flight_instructor_8',
        'person_qualification_1_instrument_rating_9',
        'person_qualification_2_multi_engine_rating_9',
        'person_qualification_3_single_engine_piston_9',
        'person_qualification_4_flight_instructor_9',
        'person_qualification_1_instrument_rating_10',
        'person_qualification_2_multi_engine_rating_10',
        'person_qualification_3_single_engine_piston_10',
        'person_qualification_4_flight_instructor_10',
        'person_qualification_2_multi_engine_rating_11',
        'person_qualification_1_instrument_rating_11',
        'person_qualification_3_single_engine_piston_11',
        'person_qualification_3_single_engine_piston_12',
        'person_qualification_2_multi_engine_rating_12',
        'person_qualification_1_instrument_rating_12',
        'person_qualification_3_single_engine_piston_13',
    ),
    'fs.pilot': (
        'pilot_souheil_matoussi',
        'pilot_ghazi_marzouk',
        'pilot_hamza_zammelli',
    ),
    'fs.instructor': (
        'instructor_youssef_khelifa',
        'instructor_anis_gharsallah',
        'instructor_houssem_arfaoui',
        'instructor_mehdi_dhifallah',
        'instructor_raouf_belghaoui',
        'instructor_ahmed_hammami',
        'instructor_nizar_amri',
        'instructor_zied_ben_saad',
        'instructor_yosr_gtari',
        'instructor_ahmed_koubaa',
    ),
}

GENERIC_REFERENCES = (
    ('ir.attachment', 'res_model', 'res_id', ()),
    ('mail.activity', 'res_model', 'res_id', ()),
    ('mail.followers', 'res_model', 'res_id', ()),
    (
        'mail.message',
        'model',
        'res_id',
        (('message_type', '!=', 'notification'),),
    ),
    ('mail.scheduled.message', 'model', 'res_id', ()),
)


def _referenced_record_ids(env, model_name, record_ids):
    """Return records referenced by independent stored Many2one fields."""
    if not record_ids:
        return set()

    referenced_ids = set()
    for model_class in env.registry.values():
        if model_class._abstract or not model_class._auto:
            continue
        for field in model_class._fields.values():
            if (
                field.type != 'many2one'
                or not field.store
                or field.compute
                or field.related
                or field.comodel_name != model_name
            ):
                continue
            references = env[model_class._name].sudo().with_context(
                active_test=False,
            ).search([(field.name, 'in', record_ids)])
            referenced_ids.update(references.mapped(field.name).ids)
    for (
        reference_model,
        model_field,
        record_id_field,
        extra_domain,
    ) in GENERIC_REFERENCES:
        if reference_model not in env.registry:
            continue
        reference_domain = [
            (model_field, '=', model_name),
            (record_id_field, 'in', record_ids),
            *extra_domain,
        ]
        references = env[reference_model].sudo().search(reference_domain)
        referenced_ids.update(references.mapped(record_id_field))
    return referenced_ids


def _remove_legacy_records(env, model_name, xml_id_names):
    """Remove only unreferenced records identified by former fs_people XML IDs."""
    external_ids = env['ir.model.data'].sudo().search([
        ('module', '=', 'fs_people'),
        ('model', '=', model_name),
        ('name', 'in', xml_id_names),
    ])
    records = env[model_name].sudo().browse(external_ids.mapped('res_id')).exists()
    existing_ids = set(records.ids)
    referenced_ids = _referenced_record_ids(env, model_name, existing_ids)
    removable_records = records.filtered(lambda record: record.id not in referenced_ids)
    removed_ids = set()
    for record in removable_records:
        record_id = record.id
        try:
            # Dependent modules may not yet be registered in this migration
            # stage. Let the database protect any fixture still referenced by
            # a foreign key from a later-loaded module.
            with env.cr.savepoint():
                record.unlink()
        except IntegrityError:
            continue
        removed_ids.add(record_id)

    # unlink() can cascade to ir.model.data, so never reuse the pre-unlink
    # recordset when cleaning external IDs.
    external_ids = env['ir.model.data'].sudo().search([
        ('module', '=', 'fs_people'),
        ('model', '=', model_name),
        ('name', 'in', xml_id_names),
    ])
    existing_record_ids = set(
        env[model_name].sudo().browse(external_ids.mapped('res_id')).exists().ids
    )
    stale_external_ids = external_ids.filtered(
        lambda external_id: external_id.res_id not in existing_record_ids
    )
    stale_external_ids.unlink()


def migrate(cr, version):
    """Remove obsolete personnel fixtures without cascading into user data."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    for model_name in ('fs.person.qualification', 'fs.pilot', 'fs.instructor'):
        _remove_legacy_records(env, model_name, LEGACY_XML_IDS[model_name])
