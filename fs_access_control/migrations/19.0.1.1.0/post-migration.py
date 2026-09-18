# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Backfill the explicit subject field for legacy audit rows."""
    api.Environment(cr, SUPERUSER_ID, {})
    cr.execute(
        """
        UPDATE fs_access_audit_log
           SET subject_user_id = user_id,
               actor_id = COALESCE(actor_id, create_uid)
         WHERE subject_user_id IS NULL
            OR actor_id IS NULL
        """
    )
