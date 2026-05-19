# -*- coding: utf-8 -*-
# Part of Flight School Management System

"""Initialize the Flight School People models package.

Purpose:
    Imports models modules so Odoo can register their models, wizards, and extensions.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from . import fs_rank
from . import fs_license_type
from . import fs_qualification_type
from . import fs_english_level
from . import fs_medical_class
from . import fs_person_identity
from . import fs_person_role_transition
from . import fs_person
from . import fs_person_qualification
from . import fs_instructor
from . import fs_instructor_availability
from . import fs_student
from . import fs_pilot
from . import fs_admin_staff
from . import res_users
from . import res_config_settings
