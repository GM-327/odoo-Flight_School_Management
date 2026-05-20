# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Drop the former class-type activity uniqueness constraint.

    OR requirement groups allow the same activity to appear in multiple groups
    for the same class type, so duplicate validation now lives in Python with
    group-aware scope rules.
    """
    cr.execute("""
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            FOR constraint_name IN
                SELECT pg_constraint.conname
                  FROM pg_constraint
                  JOIN pg_class
                    ON pg_class.oid = pg_constraint.conrelid
                 WHERE pg_class.relname = 'fs_class_type_hours'
                   AND pg_constraint.contype = 'u'
                   AND ARRAY(
                       SELECT pg_attribute.attname::text
                         FROM unnest(pg_constraint.conkey) WITH ORDINALITY AS cols(attnum, ord)
                         JOIN pg_attribute
                           ON pg_attribute.attrelid = pg_constraint.conrelid
                          AND pg_attribute.attnum = cols.attnum
                        ORDER BY cols.ord
                   ) = ARRAY['class_type_id', 'activity_id']
            LOOP
                EXECUTE format('ALTER TABLE fs_class_type_hours DROP CONSTRAINT %I', constraint_name);
            END LOOP;
        END $$;
    """)
