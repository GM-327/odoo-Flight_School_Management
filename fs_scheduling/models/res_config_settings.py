# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight school scheduling module."""

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
