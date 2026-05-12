# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models

# === Constants (Fallback Defaults) ===
# These are fallback values used when config parameters are not set.
# Actual values should be read from ir.config_parameter via the helper methods.
PILOT_FUNCTION_SELECTION = [
    ('student', 'Student'),
    ('solo', 'Solo'),
    ('instructor', 'Instructor'),
    ('safety_pilot', 'Safety Pilot'),
    ('supervisor', 'Supervisor'),
    ('pilot', 'Pilot'),
]

FLIGHT_CATEGORY_SELECTION = [
    ('student_training', '📚 Student Training'),
    ('staff_training', '👥 Pilot/Staff Training'),
]

# ID offsets for crew member virtual model
INSTRUCTOR_ID_OFFSET = 1000000
PILOT_ID_OFFSET = 2000000

# Scheduling defaults (related to res.config.settings)
# See: fs_scheduling/models/res_config_settings.py
DEFAULT_ADD_THRESHOLD = 7000          # flight_school.first_added_mission_number
DEFAULT_SLOT_INCREMENT_MINUTES = 15   # flight_school.scheduling_time_slot_minutes
DEFAULT_BUFFER_MINUTES = 15           # flight_school.scheduling_buffer_minutes


class FsFlightMixin(models.AbstractModel):
    """Mixin providing common flight fields, methods, and utilities.

    This mixin centralizes duplicated logic across fs.flight, fs.scheduled.flight,
    and various wizard models to ensure consistency and reduce code duplication.
    """
    _name = 'fs.flight.mixin'
    _description = 'Common Flight Fields and Methods Mixin'

    # === Utility Methods ===

    @api.model
    def _get_callsign_config(self):
        """Get callsign configuration from system parameters."""
        ICP = self.env['ir.config_parameter'].sudo()
        return {
            'prefix': ICP.get_param('flight_school.mission_callsign_prefix', 'ABS'),  # type: ignore
            # type: ignore
            'threshold': int(ICP.get_param('flight_school.first_added_mission_number', str(DEFAULT_ADD_THRESHOLD))),
        }

    @api.model
    def _get_scheduling_config(self):
        """Get scheduling configuration from system parameters.

        Returns:
            dict with keys:
                - slot_increment: Time slot increment in hours (e.g., 0.25 = 15 minutes)
                - buffer_minutes: Buffer time between flights in minutes
        """
        ICP = self.env['ir.config_parameter'].sudo()
        slot_minutes = int(ICP.get_param(  # type: ignore
            'flight_school.scheduling_time_slot_minutes',
            str(DEFAULT_SLOT_INCREMENT_MINUTES),
        ))
        buffer_minutes = int(ICP.get_param(  # type: ignore
            'flight_school.scheduling_buffer_minutes',
            str(DEFAULT_BUFFER_MINUTES),
        ))
        return {
            'slot_increment': slot_minutes / 60.0,  # Convert to hours
            'buffer_minutes': buffer_minutes,
        }

    @api.model
    def _get_next_callsign(self, is_sim=False, exclude_id=None, date=None):
        """Generate the next available callsign.

        Args:
            is_sim: If True, generate SIM prefix callsign (SIM0001, SIM0002...)
            exclude_id: Record ID to exclude from search (for updates)
            date: Date context for year-based filtering

        Returns:
            str: Next available callsign (e.g., 'ABS0042' or 'SIM0001')
        """
        if date is None:
            date = fields.Date.context_today(self)

        # Year range for filtering
        start_year = date.replace(month=1, day=1)
        end_year = date.replace(month=12, day=31)

        if is_sim:
            prefix = 'SIM'
            # Search in both scheduled flights and actual flights
            scheduled_data = self.env['fs.scheduled.flight'].search_read([
                ('callsign', '=like', f'{prefix}%'),
                ('date', '>=', start_year),
                ('date', '<=', end_year),
            ], ['callsign'])

            flight_model = self.env.get('fs.flight')
            flight_data = flight_model.search_read([
                ('callsign', '=like', f'{prefix}%'),
                ('date', '>=', start_year),
                ('date', '<=', end_year),
            ], ['callsign']) if flight_model is not None else []

            all_data = scheduled_data + flight_data

            max_num = 0
            for data in all_data:
                c = data['callsign']
                if isinstance(c, str) and c.startswith(prefix) and len(c) > len(prefix):
                    suffix = c[len(prefix):]
                    if suffix.isdigit():
                        val = int(suffix)
                        if val > max_num:
                            max_num = val

            next_num = max_num + 1
            return f"{prefix}{next_num:04d}"
        else:
            config = self._get_callsign_config()
            prefix = config['prefix']
            threshold = config['threshold']

            # Build domain
            domain = [
                ('callsign', '=like', f'{prefix}%'),
                ('date', '>=', start_year),
                ('date', '<=', end_year),
                ('callsign', '!=', False),
                ('callsign', '!=', 'ADD'),
            ]
            if exclude_id:
                domain.append(('id', '!=', exclude_id))

            # Search in both scheduled flights and actual flights
            scheduled_data = self.env['fs.scheduled.flight'].search_read(domain, ['callsign'])

            flight_domain = [
                ('callsign', '=like', f'{prefix}%'),
                ('date', '>=', start_year),
                ('date', '<=', end_year),
                ('callsign', '!=', False),
                ('callsign', '!=', 'ADD'),
            ]
            if exclude_id and self._name == 'fs.flight':
                flight_domain.append(('id', '!=', exclude_id))

            flight_model = self.env.get('fs.flight')
            flight_data = flight_model.search_read(flight_domain, ['callsign']) if flight_model is not None else []

            all_data = scheduled_data + flight_data

            # Find max number below threshold (for regular scheduled flights)
            max_num = 0
            for data in all_data:
                c = data['callsign']
                if isinstance(c, str) and c.startswith(prefix) and len(c) > len(prefix):
                    suffix = c[len(prefix):]
                    if suffix.isdigit():
                        val = int(suffix)
                        if val < threshold and val > max_num:
                            max_num = val

            next_num = max_num + 1
            return f"{prefix}{next_num:04d}"

    @api.model
    def _get_next_add_callsign(self, exclude_id=None, date=None):
        """Generate the next available ADD callsign (above threshold).

        ADD callsigns are used for ad-hoc/extra flights added during operations.
        They start from the configured threshold (default 7000) and increment.

        Args:
            exclude_id: Record ID to exclude from search
            date: Date context for year-based filtering

        Returns:
            str: Next available ADD callsign (e.g., 'ABS7001')
        """
        if date is None:
            date = fields.Date.context_today(self)

        config = self._get_callsign_config()
        prefix = config['prefix']
        threshold = config['threshold']

        # Year range
        start_year = date.replace(month=1, day=1)
        end_year = date.replace(month=12, day=31)

        # Build domain
        domain = [
            ('date', '>=', start_year),
            ('date', '<=', end_year),
            ('callsign', '!=', False),
            ('callsign', '!=', 'ADD'),
        ]
        if exclude_id:
            domain.append(('id', '!=', exclude_id))

        flight_model = self.env.get('fs.flight')
        flight_data = flight_model.search_read(domain, ['callsign']) if flight_model is not None else []

        # Find max number at or above threshold
        max_num = threshold - 1  # So first ADD is exactly threshold
        for data in flight_data:
            c = data['callsign']
            if isinstance(c, str) and c.startswith(prefix) and len(c) > len(prefix):
                suffix = c[len(prefix):]
                if suffix.isdigit():
                    val = int(suffix)
                    if val >= threshold and val > max_num:
                        max_num = val

        next_num = max_num + 1
        return f"{prefix}{next_num}"

    @api.model
    def _format_hours_display(self, hours_float):
        """Format a float hours value to HH:MM string.

        Args:
            hours_float: Hours as float (e.g., 1.5 = 1:30)

        Returns:
            str: Formatted time string (e.g., '01:30')
        """
        if not hours_float:
            return "00:00"
        hours = int(hours_float)
        minutes = int((hours_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"

    def _compute_crew_warning_html(self, pilot1_crew, pilot2_crew, flight_category):
        """Compute HTML warning for crew issues.

        Args:
            pilot1_crew: Pilot 1 crew member record
            pilot2_crew: Pilot 2 crew member record
            flight_category: 'student_training' or 'staff_training'

        Returns:
            str or False: HTML warning string or False if no warnings
        """
        warnings = []

        if pilot1_crew:
            if pilot1_crew.has_expired_qualification:
                warnings.append(f"<strong>{pilot1_crew.name}</strong> has expired qualifications/medical.")
            if flight_category == 'staff_training' and pilot1_crew.member_type == 'student':
                warnings.append(f"<strong>{pilot1_crew.name}</strong> is a student (Staff Training selected).")

        if pilot2_crew:
            if pilot2_crew.has_expired_qualification:
                warnings.append(f"<strong>{pilot2_crew.name}</strong> has expired qualifications/medical.")
            if flight_category == 'staff_training' and pilot2_crew.member_type == 'student':
                warnings.append(f"<strong>{pilot2_crew.name}</strong> is a student (Staff Training selected).")

        if warnings:
            return (
                "<div class='alert alert-warning p-2 mb-0' role='alert'>"
                "<i class='fa fa-exclamation-triangle me-2'/>" +
                " | ".join(warnings) +
                "</div>"
            )
        return False

    def _get_pilot_function_from_member_type(self, member_type, is_solo=False):
        """Determine pilot function based on crew member type.

        Args:
            member_type: 'student', 'instructor', or 'pilot'
            is_solo: If True and member is student, return 'solo'

        Returns:
            str: Appropriate pilot function selection value
        """
        if member_type == 'student':
            return 'solo' if is_solo else 'student'
        elif member_type == 'instructor':
            return 'instructor'
        else:
            return 'pilot'

    def _compute_is_sim_from_mission_activity(self, mission_id, activity_id):
        """Determine if flight is simulator based on mission or activity.

        Args:
            mission_id: fs.flight.mission record or False
            activity_id: fs.flight.activity record or False

        Returns:
            bool: True if simulator session
        """
        if mission_id:
            return mission_id.is_sim
        elif activity_id:
            return activity_id.is_sim
        return False

    def _get_instructor_from_enrollment(self, enrollment):
        """Get instructor crew member from student enrollment.

        Args:
            enrollment: fs.student.enrollment record

        Returns:
            fs.crew.member record or False
        """
        if not enrollment:
            return False

        instructor = enrollment.instructor_id
        if instructor and not instructor.has_expired_qualification:
            crew_member = self.env['fs.crew.member'].search([
                ('source_model', '=', 'fs.instructor'),
                ('source_id', '=', instructor.id),
            ], limit=1)
            return crew_member
        return False
