# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Scheduling res config settings module.

Purpose:
    Defines classes ResConfigSettings for planned flights, crew selection, route management, scheduling wizards, conflict detection, and timeline data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_training, fs_fleet, fs_people, mail, web_timeline.
    fs_flights publishes scheduled plans to operations boards.
"""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight school scheduling module.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _inherit: Odoo model(s) extended by this class: ``res.config.settings``.

    Related:
        fs_flights publishes scheduled plans to operations boards.
        fs_fleet supplies aircraft availability.
    """

    _inherit = 'res.config.settings'

    # === Scheduling Settings ===
    fs_mission_callsign_prefix = fields.Char(
        string='Mission Callsign Prefix',
        default='ABS',
        config_parameter='flight_school.mission_callsign_prefix',
        help="Default prefix for flight mission callsigns.",
    )
    fs_first_added_mission_number = fields.Integer(
        string='First Added Mission Number',
        default=7000,
        config_parameter='flight_school.first_added_mission_number',
        help="Threshold for added missions. Regular missions use numbers below this value, resetting yearly.",
    )
    fs_scheduling_buffer_minutes = fields.Integer(
        string='Scheduling Buffer (Minutes)',
        default=15,
        config_parameter='flight_school.scheduling_buffer_minutes',
        help="Default buffer time between missions for the same instructor or aircraft.",
    )
    fs_scheduling_time_slot_minutes = fields.Integer(
        string='Time Slot Granularity (Minutes)',
        default=15,
        config_parameter='flight_school.scheduling_time_slot_minutes',
        help="Default time slot increment for scheduling (e.g., 15 minutes).",
    )

    @api.constrains('fs_scheduling_buffer_minutes')
    def _check_scheduling_buffer_minutes(self):
        """Keep the conflict buffer within a practical, non-negative range."""
        for settings in self:
            if not 0 <= settings.fs_scheduling_buffer_minutes <= 720:
                raise ValidationError(_(
                    "Scheduling buffer must be between 0 and 720 minutes."
                ))

    @api.constrains('fs_scheduling_time_slot_minutes')
    def _check_scheduling_time_slot_minutes(self):
        """Require a whole-hour divisor so generated times remain exact slots."""
        for settings in self:
            slot_minutes = settings.fs_scheduling_time_slot_minutes
            if not 1 <= slot_minutes <= 60 or 60 % slot_minutes:
                raise ValidationError(_(
                    "Time slot granularity must be a divisor of 60 between 1 and 60 minutes."
                ))
