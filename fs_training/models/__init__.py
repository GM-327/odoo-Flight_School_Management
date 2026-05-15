# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Initialize the Flight School Training models package.

Purpose:
    Imports models modules so Odoo can register their models, wizards, and extensions.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
from . import fs_flight_discipline
from . import fs_flight_type
from . import fs_flight_activity
from . import fs_class_requirement
from . import fs_class_type
from . import fs_flight_mission
from . import fs_admin_task
from . import fs_training_class
from . import fs_student_enrollment
from . import fs_mission_completion
from . import fs_student
from . import fs_instructor
from . import fs_training_dashboard
from . import res_config_settings
