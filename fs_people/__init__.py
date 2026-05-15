# -*- coding: utf-8 -*-
# Part of Flight School Management System

"""Initialize the Flight School People addon package.

Purpose:
    Loads the addon subpackages that implement students, instructors, pilots, administrative staff, qualifications, licenses, and medical tracking.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from . import models
from . import wizard
