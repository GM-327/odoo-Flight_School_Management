# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Initialize the Flight School Fleet models package.

Purpose:
    Imports models modules so Odoo can register their models, wizards, and extensions.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training defines aircraft-type requirements.
"""
from . import aircraft_category
from . import aircraft_type
from . import aircraft
from . import fs_fleet_dashboard
from . import res_config_settings
