# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Initialize the Flight School Settings models package.

Purpose:
    Imports models modules so Odoo can register their models, wizards, and extensions.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: base, base_setup, auth_signup.
    All Flight School addons consume the groups, menu roots, and shared settings defined here.
"""
from . import fs_department
from . import res_config_settings
