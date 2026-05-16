# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Initialize the Flight School Documents models package.

Purpose:
    Imports models modules so Odoo can register their models, wizards, and extensions.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: web, fs_core, fs_people, fs_training.
    fs_people and fs_training provide the related business entities whose files are managed here.
"""
from . import fs_document_type
from . import fs_document
from . import fs_document_version
from . import fs_student
from . import fs_instructor
from . import fs_pilot
from . import fs_training_class
from . import fs_class_type
from . import fs_admin_task
from . import fs_documents_dashboard
from . import res_config_settings
