# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fs_mission_callsign_prefix = fields.Char(
        string='Mission Callsign Prefix',
        default='ABS',
        config_parameter='flight_school.mission_callsign_prefix',
        help="Default prefix for flight mission callsigns.",
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
