# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Initialize the Flight School Documents wizard package.

Purpose:
    Imports wizard modules so Odoo can register their models, wizards, and extensions.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: web, fs_core, fs_people, fs_training.
    fs_people and fs_training provide the related business entities whose files are managed here.
"""
from . import fs_document_upload_wizard
