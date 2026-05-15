# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).


"""Initialize the Flight School Scheduling models package.

Purpose:
    Imports models modules so Odoo can register their models, wizards, and extensions.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_training, fs_fleet, fs_people, mail, web_timeline.
    fs_flights publishes scheduled plans to operations boards.
"""
from . import fs_flight_mixin
from . import fs_pilot_function
from . import fs_cancellation_reason
from . import fs_crew_member
from . import fs_custom_flight_type
from . import fs_scheduled_flight
from . import res_config_settings
from . import fs_scheduling_inherits
from . import fs_flight_route
