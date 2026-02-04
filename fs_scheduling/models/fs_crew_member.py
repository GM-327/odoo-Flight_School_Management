# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, tools

STATUS_SELECTION = [
    ('valid', 'Valid'),
    ('expiring', 'Expiring Soon'),
    ('expired', 'Expired'),
    ('no_expiry', 'No Expiry'),
]


class FsCrewMember(models.Model):
    """Unified view of all crew members (students, instructors, pilots) for scheduling.
    
    This is a SQL view-based model that combines fs.student, fs.instructor, and fs.pilot
    into a single selectable list for crew assignment.
    """
    _name = 'fs.crew.member'
    _description = 'Crew Member'
    _auto = False  # This is a SQL view
    _order = 'member_type, name'

    name = fields.Char(string='Callsign', readonly=True)
    full_name = fields.Char(string='Full Name', readonly=True)
    display_name = fields.Char(string='Display Name', readonly=True)
    member_type = fields.Selection([
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('pilot', 'Pilot'),
    ], string='Type', readonly=True)
    source_id = fields.Integer(string='Source ID', readonly=True)
    source_model = fields.Char(string='Source Model', readonly=True)
    has_expired_qualification = fields.Boolean(string='Has Expired', readonly=True)
    department_id = fields.Many2one('fs.department', string='Department', readonly=True)
    
    # === Expiry Status Fields ===
    medical_status = fields.Selection(STATUS_SELECTION, string='Medical', readonly=True)
    english_status = fields.Selection(STATUS_SELECTION, string='English', readonly=True)
    license_status = fields.Selection(STATUS_SELECTION, string='License', readonly=True)
    security_status = fields.Selection(STATUS_SELECTION, string='Security', readonly=True)
    insurance_status = fields.Selection(STATUS_SELECTION, string='Insurance', readonly=True)
    
    # Computed HTML badges field for qualifications/license
    qualification_badges = fields.Html(
        string='Qualifications',
        compute='_compute_qualification_badges',
        sanitize=False,
    )
    
    earliest_expiry_date = fields.Date(string='Earliest Expiry', readonly=True)
    # For students - enrollment reference
    enrollment_id = fields.Integer(string='Enrollment ID', readonly=True)

    def init(self):
        """Create or replace the SQL view."""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                -- Students (via enrollment)
                SELECT 
                    e.id AS id,
                    COALESCE(e.callsign, s.name) AS name,
                    s.name AS full_name,
                    COALESCE(e.callsign, s.name) AS display_name,
                    'student' AS member_type,
                    s.id AS source_id,
                    'fs.student.enrollment' AS source_model,
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
                WHERE e.status IN ('active', 'solo')
                  AND s.active = True
                
                UNION ALL
                
                -- Instructors
                SELECT 
                    i.id + 1000000 AS id,
                    COALESCE(i.callsign, i.name) AS name,
                    i.name AS full_name,
                    COALESCE(i.callsign, i.name) AS display_name,
                    'instructor' AS member_type,
                    i.id AS source_id,
                    'fs.instructor' AS source_model,
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
                WHERE i.active = True
                
                UNION ALL
                
                -- Pilots
                SELECT 
                    p.id + 2000000 AS id,
                    COALESCE(p.callsign, p.name) AS name,
                    p.name AS full_name,
                    COALESCE(p.callsign, p.name) AS display_name,
                    'pilot' AS member_type,
                    p.id AS source_id,
                    'fs.pilot' AS source_model,
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
                WHERE p.active = True
            )
        """ % self._table)

    @api.depends('name')
    def _compute_display_name(self):
        """Compute display name (prioritizing callsign)."""
        for record in self:
            record.display_name = record.name or ''

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        """Search by name (callsign) or full_name."""
        domain = domain or []
        if name:
            domain = ['|', ('name', operator, name), ('full_name', operator, name)] + domain
        return self._search(domain, limit=limit, order=order)

    def get_source_record(self):
        """Return the actual student/instructor/pilot record."""
        self.ensure_one()
        if self.source_model and self.source_id:
            return self.env[self.source_model].browse(self.source_id)
        return False
    
    def get_enrollment_record(self):
        """Return the enrollment record for students."""
        self.ensure_one()
        if self.member_type == 'student' and self.enrollment_id:
            return self.env['fs.student.enrollment'].browse(self.enrollment_id)
        return False

    @api.depends('member_type', 'source_model', 'source_id', 'license_status')
    def _compute_qualification_badges(self):
        """Compute HTML badges for qualifications (instructors/pilots) or license (students)."""
        status_colors = {
            'valid': '#28a745',      # Green
            'expiring': '#ffc107',   # Yellow
            'expired': '#dc3545',    # Red
            'no_expiry': '#6c757d',  # Gray
        }
        for record in self:
            badges_html = ''
            
            if record.member_type in ('instructor', 'pilot'):
                # Get qualification badges from source record
                source = record.get_source_record()
                if source and hasattr(source, 'qualification_badges'):
                    badges_html = source.qualification_badges or ''  # type: ignore
            
            elif record.member_type == 'student':
                # Generate license badge for students
                if record.license_status:
                    color = status_colors.get(record.license_status, '#6c757d')  # type: ignore
                    text_color = '#212529' if record.license_status == 'expiring' else '#ffffff'
                    label = 'SC'
                    badges_html = (
                        f'<span style="background-color: {color}; color: {text_color}; '
                        f'padding: 2px 8px; border-radius: 4px; margin-right: 4px; '
                        f'font-size: 12px; display: inline-block;">'
                        f'{label}</span>'
                    )
            
            record.qualification_badges = badges_html
