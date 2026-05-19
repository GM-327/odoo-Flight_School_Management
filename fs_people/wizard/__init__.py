# -*- coding: utf-8 -*-
# Part of Flight School Management System

"""Initialize the Flight School People wizard package.

Purpose:
    Imports wizard modules so Odoo can register their models, wizards, and extensions.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from . import fs_people_dashboard
from . import fs_person_role_transition_wizard
