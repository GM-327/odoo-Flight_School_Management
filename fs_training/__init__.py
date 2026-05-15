# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Initialize the Flight School Training addon package.

Purpose:
    Loads the addon subpackages that implement class types, training classes, enrollments, missions, activities, completion tracking, and training KPIs.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
from . import models
