# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Initialize the Flight School Flights wizards package.

Purpose:
    Imports wizards modules so Odoo can register their models, wizards, and extensions.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_scheduling, fs_fleet, fs_training, fs_people, mail, bus.
    fs_scheduling provides planned flights.
"""
from . import fs_add_flight_wizard
from . import fs_flight_cancel_wizard
from . import fs_flight_delete_wizard
from . import fs_import_schedule_wizard
from . import fs_recalculate_hours_wizard
