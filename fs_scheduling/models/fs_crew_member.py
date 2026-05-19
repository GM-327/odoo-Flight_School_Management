# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Scheduling fs crew member module.

Purpose:
    Defines classes FsCrewMember for planned flights, crew selection, route management, scheduling wizards, conflict detection, and timeline data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_training, fs_fleet, fs_people, mail, web_timeline.
    fs_flights publishes scheduled plans to operations boards.
"""
from collections import defaultdict

from markupsafe import Markup
from psycopg2 import sql

from odoo import api, fields, models, tools

STATUS_SELECTION = [
    ('valid', 'Valid'),
    ('expiring', 'Expiring Soon'),
    ('expired', 'Expired'),
    ('no_expiry', 'No Expiry'),
]

MEMBER_TYPE_SELECTION = [
    ('student', 'Student'),
    ('instructor', 'Instructor'),
    ('pilot', 'Pilot'),
]

ROLE_STATE_SELECTION = [
    ('current', 'Current'),
    ('former', 'Former'),
]

ALLOWED_SOURCE_MODELS = frozenset({
    'fs.student',
    'fs.instructor',
    'fs.pilot',
})
QUALIFICATION_SOURCE_TYPES = ('instructor', 'pilot')

# Offsets keep IDs unique across the three source tables inside one SQL view.
VIEW_ID_OFFSETS = {
    'student': 0,
    'instructor': 1000000,
    'pilot': 2000000,
}
STATUS_COLORS = {
    'valid': '#28a745',
    'expiring': '#ffc107',
    'expired': '#dc3545',
    'no_expiry': '#6c757d',
}
DEFAULT_BADGE_COLOR = '#6c757d'
DEFAULT_BADGE_TEXT_COLOR = '#ffffff'
EXPIRING_BADGE_TEXT_COLOR = '#212529'
BADGE_STYLE = (
    'padding: 2px 8px; border-radius: 4px; margin-right: 4px; '
    'font-size: 12px; display: inline-block;'
)
STUDENT_LICENSE_BADGE_LABEL = 'SC'


class FsCrewMember(models.Model):
    """Unified SQL view of students, instructors, and pilots for scheduling.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.crew.member``.
        _description (str): Human-readable model label, ``Crew Member``.

    Related:
        fs_flights publishes scheduled plans to operations boards.
        fs_fleet supplies aircraft availability.
    """

    _name = 'fs.crew.member'
    _description = 'Crew Member'
    _auto = False
    _order = 'member_type, name'
    _rec_name = 'name'

    name = fields.Char(string='Callsign', readonly=True)
    full_name = fields.Char(string='Full Name', readonly=True)
    member_type = fields.Selection(MEMBER_TYPE_SELECTION, string='Type', readonly=True)
    source_id = fields.Integer(string='Source ID', readonly=True)
    source_model = fields.Char(string='Source Model', readonly=True)
    role_state = fields.Selection(ROLE_STATE_SELECTION, string='Role Status', readonly=True)
    source_active = fields.Boolean(string='Source Active', readonly=True)
    crew_selectable = fields.Boolean(string='Selectable', readonly=True)
    has_expired_qualification = fields.Boolean(string='Has Expired', readonly=True)
    department_id = fields.Many2one('fs.department', string='Department', readonly=True)

    medical_status = fields.Selection(STATUS_SELECTION, string='Medical', readonly=True)
    english_status = fields.Selection(STATUS_SELECTION, string='English', readonly=True)
    license_status = fields.Selection(STATUS_SELECTION, string='License', readonly=True)
    security_status = fields.Selection(STATUS_SELECTION, string='Security', readonly=True)
    insurance_status = fields.Selection(STATUS_SELECTION, string='Insurance', readonly=True)

    # sanitize=False is intentional because the HTML is generated server-side.
    qualification_badges = fields.Html(
        string='Qualifications',
        compute='_compute_qualification_badges',
        sanitize=False,
    )

    earliest_expiry_date = fields.Date(string='Earliest Expiry', readonly=True)
    enrollment_id = fields.Integer(string='Enrollment ID', readonly=True)

    @api.model
    def _get_view_query(self):
        """Return view query information used by Flight School workflows.

        Returns:
            str: Formatted display value.
        """
        return f"""
            -- Students (via enrollment)
            SELECT
                e.id + {VIEW_ID_OFFSETS['student']} AS id,
                -- Blank callsigns should fall back to the person's name, not stay empty.
                COALESCE(NULLIF(TRIM(e.callsign), ''), s.name) AS name,
                s.name AS full_name,
                'student' AS member_type,
                s.id AS source_id,
                'fs.student' AS source_model,
                COALESCE(s.role_state, 'current') AS role_state,
                s.active AS source_active,
                (
                    s.active = TRUE
                    AND COALESCE(s.role_state, 'current') = 'current'
                    AND e.status IN ('active', 'solo')
                ) AS crew_selectable,
                s.has_expired_status AS has_expired_qualification,
                NULL::integer AS department_id,
                s.medical_status AS medical_status,
                NULL::varchar AS english_status,
                s.license_expiry_status AS license_status,
                s.security_clearance_status AS security_status,
                s.insurance_status AS insurance_status,
                NULL::date AS earliest_expiry_date,
                e.id AS enrollment_id
            FROM fs_student_enrollment e
            JOIN fs_student s ON s.id = e.student_id

            UNION ALL

            -- Instructors
            SELECT
                i.id + {VIEW_ID_OFFSETS['instructor']} AS id,
                -- Normalize whitespace-only callsigns so search/display stay consistent.
                COALESCE(NULLIF(TRIM(i.callsign), ''), i.name) AS name,
                i.name AS full_name,
                'instructor' AS member_type,
                i.id AS source_id,
                'fs.instructor' AS source_model,
                COALESCE(i.role_state, 'current') AS role_state,
                i.active AS source_active,
                (i.active = TRUE AND COALESCE(i.role_state, 'current') = 'current') AS crew_selectable,
                i.has_expired_qualification AS has_expired_qualification,
                i.department_id AS department_id,
                i.medical_status AS medical_status,
                i.english_status AS english_status,
                NULL::varchar AS license_status,
                NULL::varchar AS security_status,
                NULL::varchar AS insurance_status,
                i.earliest_expiry_date AS earliest_expiry_date,
                NULL::integer AS enrollment_id
            FROM fs_instructor i

            UNION ALL

            -- Pilots
            SELECT
                p.id + {VIEW_ID_OFFSETS['pilot']} AS id,
                -- Use the same fallback rule for all crew sources exposed by the view.
                COALESCE(NULLIF(TRIM(p.callsign), ''), p.name) AS name,
                p.name AS full_name,
                'pilot' AS member_type,
                p.id AS source_id,
                'fs.pilot' AS source_model,
                COALESCE(p.role_state, 'current') AS role_state,
                p.active AS source_active,
                (p.active = TRUE AND COALESCE(p.role_state, 'current') = 'current') AS crew_selectable,
                p.has_expired_qualification AS has_expired_qualification,
                p.department_id AS department_id,
                p.medical_status AS medical_status,
                p.english_status AS english_status,
                NULL::varchar AS license_status,
                p.security_clearance_status AS security_status,
                p.insurance_status AS insurance_status,
                p.earliest_expiry_date AS earliest_expiry_date,
                NULL::integer AS enrollment_id
            FROM fs_pilot p
        """

    def init(self):
        """Create or replace the SQL view.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)

        # Interpolate the view name as an SQL identifier while keeping the body readable.
        query = sql.SQL("""
            CREATE OR REPLACE VIEW {table} AS (
                {view_query}
            )
        """).format(
            table=sql.Identifier(self._table),
            view_query=sql.SQL(self._get_view_query()),
        )
        self.env.cr.execute(query)

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        """Search by callsign or full name.

        Args:
            name: Search term or display name supplied by the caller.
            domain: Odoo domain limiting the records considered by the operation.
            operator: Search operator requested by Odoo name-search APIs.
            limit: Maximum number of records to return.
            order: Value supplied by Odoo or the calling workflow.

        Returns:
            list: Matching record identifiers and display names in Odoo format.
        """
        domain = domain or []
        if not name:
            return self._search(domain, limit=limit, order=order)

        search_domain = fields.Domain.AND([
            domain,
            fields.Domain.OR([
                [('name', operator, name)],
                [('full_name', operator, name)],
            ]),
        ])
        return self._search(search_domain, limit=limit, order=order)

    def get_source_record(self):
        """Return the linked student/instructor/pilot record if it still exists.

        Returns:
            Any: Value required by the Odoo ORM, action system, or calling workflow.
        """
        self.ensure_one()

        if not self.source_model or not self.source_id:
            return False
        if self.source_model not in ALLOWED_SOURCE_MODELS:
            return False

        # View rows can outlive deleted source records, so always collapse missing rows.
        return self.env[self.source_model].browse(self.source_id).exists()

    def get_enrollment_record(self):
        """Return the student enrollment record if it still exists.

        Returns:
            Any: Value required by the Odoo ORM, action system, or calling workflow.
        """
        self.ensure_one()
        if self.member_type != 'student' or not self.enrollment_id:
            return False

        # Use exists() for the same reason as get_source_record(): the view is read-only.
        return self.env['fs.student.enrollment'].browse(self.enrollment_id).exists()

    @api.model
    def _build_status_badge(self, status, label):
        """Build a small HTML badge for student status display.

        Args:
            status: Value supplied by Odoo or the calling workflow.
            label: Value supplied by Odoo or the calling workflow.

        Returns:
            Any: Value required by the Odoo ORM, action system, or calling workflow.
        """
        background_color = STATUS_COLORS.get(status, DEFAULT_BADGE_COLOR)
        text_color = (
            EXPIRING_BADGE_TEXT_COLOR
            if status == 'expiring'
            else DEFAULT_BADGE_TEXT_COLOR
        )
        return Markup(
            '<span style="background-color: {bg}; color: {fg}; {style}">{label}</span>'
        ).format(
            bg=background_color,
            fg=text_color,
            style=BADGE_STYLE,
            label=label,
        )

    @api.model
    def _get_source_badges_map(self, crew_members):
        """Batch-load qualification badges from source models.

        Args:
            crew_members: Value supplied by Odoo or the calling workflow.

        Returns:
            Any: Value required by the Odoo ORM, action system, or calling workflow.
        """
        source_ids_by_model = defaultdict(set)

        for member in crew_members:
            if member.source_model in ALLOWED_SOURCE_MODELS and member.source_id:
                source_ids_by_model[member.source_model].add(member.source_id)

        source_badges = {}
        for model_name, source_ids in source_ids_by_model.items():
            # Grouping by model avoids an N+1 browse pattern during badge computation.
            source_model = self.env[model_name]
            if 'qualification_badges' not in source_model._fields:
                continue

            for source_record in source_model.browse(list(source_ids)).exists():
                source_badges[(model_name, source_record.id)] = (
                    source_record.qualification_badges or False
                )

        return source_badges

    @api.depends('member_type', 'source_model', 'source_id', 'license_status')
    def _compute_qualification_badges(self):
        """Compute qualification badges for instructors/pilots and license badges for students.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        # Instructor and pilot badges already exist on their source records, so fetch them once.
        source_badges = self._get_source_badges_map(
            self.filtered(lambda member: member.member_type in QUALIFICATION_SOURCE_TYPES)
        )

        for record in self:
            if record.member_type in QUALIFICATION_SOURCE_TYPES:
                record.qualification_badges = source_badges.get(
                    (record.source_model, record.source_id),
                    False,
                )
            elif record.member_type == 'student' and record.license_status:
                record.qualification_badges = self._build_status_badge(
                    record.license_status,
                    STUDENT_LICENSE_BADGE_LABEL,
                )
            else:
                record.qualification_badges = False
