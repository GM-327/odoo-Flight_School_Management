# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Training fs student enrollment module.

Purpose:
    Defines classes FsStudentEnrollment, FsEnrollmentHours for class types, training classes, enrollments, missions, activities, completion tracking, and training KPIs.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


ENROLLMENT_REQUIREMENT_GROUP_COUNT_AS_SELECTION = [
    ('aircraft', 'Aircraft'),
    ('simulator', 'Simulator'),
    ('unallocated', 'Unallocated'),
]

ENROLLMENT_REQUIREMENT_ROLE_SELECTION = [
    ('standalone', 'Mandatory'),
    ('alternative', 'OR Alternative'),
]


class FsStudentEnrollment(models.Model):
    """Student enrollment in a training class.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.student.enrollment``.
        _inherit: Odoo model(s) extended by this class: ``['mail.thread', 'mail.activity.mixin']``.
        _description (str): Human-readable model label, ``Student Enrollment``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

    _name = 'fs.student.enrollment'
    _description = 'Student Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'callsign'
    _order = 'training_class_id, student_id'

    _unique_student_class = models.Constraint(
        'UNIQUE(student_id, training_class_id)',
        'This student is already enrolled in this class!',
    )

    # === Enrolled person (mutually exclusive: student_id OR pilot_id/enrolled_instructor_id) ===
    student_id = fields.Many2one(
        comodel_name='fs.student',
        string='Student',
        tracking=True,
        ondelete='restrict',
        domain="['!', ('enrollment_ids.status', 'in', ['enrolled', 'active'])]",
    )
    pilot_id = fields.Many2one(
        comodel_name='fs.pilot',
        string='Pilot',
        tracking=True,
        ondelete='restrict',
        domain="[('active', '=', True)]",
        help="Licensed pilot enrolled in this class (for licensed-personnel classes only).",
    )
    enrolled_instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Instructor (enrolled)',
        tracking=True,
        ondelete='restrict',
        domain="[('active', '=', True)]",
        help="Instructor enrolled in this class (for licensed-personnel classes only).",
    )
    # Single Reference proxy used in the list-view column to select either a pilot or instructor.
    # Stored; an onchange keeps pilot_id / enrolled_instructor_id in sync.
    licensed_person_ref = fields.Reference(
        selection=[('fs.pilot', 'Pilot'), ('fs.instructor', 'Instructor')],
        string='Enrolled Person',
        compute='_compute_licensed_person_ref',
        inverse='_inverse_licensed_person_ref',
        store=True,
        help="Select the pilot or instructor enrolled in this class.",
    )
    # Flag mirrored from the training class for easy domain/visibility use
    for_licensed_personnel = fields.Boolean(
        related='training_class_id.for_licensed_personnel',
        string='For Licensed Personnel',
        store=True,
    )
    enrolled_person_name = fields.Char(
        string='Enrolled Person Name',
        compute='_compute_enrolled_person_name',
        store=True,
        help="Display name of the enrolled person (student, pilot, or instructor).",
    )
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        string='Training Class',
        required=True,
        tracking=True,
        ondelete='cascade',
    )
    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Assigned Instructor',
        tracking=True,
        ondelete='restrict',
        domain="[('active', '=', True)]",
        help="Instructor assigned to supervise this student in this class.",
    )
    class_aircraft_type_ids = fields.Many2many(
        related='training_class_id.aircraft_type_ids',
        string='Class Aircraft Types',
    )
    aircraft_type_id = fields.Many2one(
        comodel_name='fs.aircraft.type',
        string='Assigned Aircraft Type',
        tracking=True,
        ondelete='restrict',
        domain="[('id', 'in', class_aircraft_type_ids)]",
        help="Specific aircraft type assigned to this student. Required when class has multiple aircraft types.",
    )
    callsign = fields.Char(
        string='Callsign',
        help="Student's callsign for this class. Auto-suggested as ClassCode + Letter (e.g., CPL24A).",
    )
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('pilot_id', 'enrolled_instructor_id')
    def _compute_licensed_person_ref(self):
        """Build the Reference value from the concrete pilot/instructor Many2one.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            if record.pilot_id:
                record.licensed_person_ref = record.pilot_id
            elif record.enrolled_instructor_id:
                record.licensed_person_ref = record.enrolled_instructor_id
            else:
                record.licensed_person_ref = False

    def _inverse_licensed_person_ref(self):
        """Propagate Reference selection back to the concrete pilot/instructor Many2one.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            ref = record.licensed_person_ref
            if ref and ref._name == 'fs.pilot':  # type: ignore[union-attr]
                record.pilot_id = ref  # type: ignore[assignment]
                record.enrolled_instructor_id = False
            elif ref and ref._name == 'fs.instructor':  # type: ignore[union-attr]
                record.enrolled_instructor_id = ref  # type: ignore[assignment]
                record.pilot_id = False
            else:
                record.pilot_id = False
                record.enrolled_instructor_id = False

    @api.depends('pilot_id', 'enrolled_instructor_id', 'student_id')
    def _compute_enrolled_person_name(self):
        """Compute enrolled person name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            if record.pilot_id:
                record.enrolled_person_name = record.pilot_id.display_name
            elif record.enrolled_instructor_id:
                record.enrolled_person_name = record.enrolled_instructor_id.display_name
            else:
                record.enrolled_person_name = record.student_id.display_name if record.student_id else False

    @api.depends('callsign', 'student_id.name', 'pilot_id.display_name', 'enrolled_instructor_id.display_name')
    def _compute_display_name(self):
        """Compute display name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            if record.callsign:
                record.display_name = record.callsign
            elif record.student_id:
                record.display_name = record.student_id.display_name or _("New Enrollment")
            elif record.pilot_id:
                record.display_name = record.pilot_id.display_name or _("New Enrollment")
            elif record.enrolled_instructor_id:
                record.display_name = record.enrolled_instructor_id.display_name or _("New Enrollment")
            else:
                record.display_name = _("New Enrollment")

    @api.onchange('licensed_person_ref')
    def _onchange_licensed_person_ref(self):
        """When the Reference widget changes, sync pilot_id/enrolled_instructor_id
        and copy the person's own callsign (for licensed-personnel classes).

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        ref = self.licensed_person_ref  # type: ignore
        if ref and ref._name == 'fs.pilot':  # type: ignore[union-attr]
            self.pilot_id = ref  # type: ignore[assignment]
            self.enrolled_instructor_id = False
        elif ref and ref._name == 'fs.instructor':  # type: ignore[union-attr]
            self.enrolled_instructor_id = ref  # type: ignore[assignment]
            self.pilot_id = False
        else:
            self.pilot_id = False
            self.enrolled_instructor_id = False
        # Copy the person's callsign immediately
        if ref and self.for_licensed_personnel:  # type: ignore
            self.callsign = getattr(ref, 'callsign', '') or ''

    @api.onchange('pilot_id', 'enrolled_instructor_id')
    def _onchange_licensed_person_callsign(self):
        """For licensed-personnel classes: copy the pilot/instructor's own callsign.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if not self.for_licensed_personnel:  # type: ignore
            return
        person = self.pilot_id or self.enrolled_instructor_id  # type: ignore
        if person:
            self.callsign = person.callsign or ''  # type: ignore[union-attr]

    @api.onchange('training_class_id', 'student_id')
    def _onchange_student_id_suggest_callsign(self):
        """For regular classes: suggest a callsign as ClassCode + incrementing letter.
        Supports batch adding by checking sibling lines in the UI.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.for_licensed_personnel:  # type: ignore
            return  # handled by _onchange_licensed_person_callsign
        if self.training_class_id and self.training_class_id.code and not self.callsign:  # type: ignore
            class_code = self.training_class_id.code  # type: ignore

            # Count sibling lines to find the next letter slot
            count = 0
            if self.training_class_id.enrollment_ids:  # type: ignore
                existing_callsigns = self.training_class_id.enrollment_ids.mapped('callsign')  # type: ignore
                count = len([c for c in existing_callsigns if c])
            else:
                count = self.env['fs.student.enrollment'].search_count([
                    ('training_class_id', '=', self.training_class_id.id),
                ])

            # Generate next letter (A=0, B=1, …)
            if count < 26:
                next_letter = chr(ord('A') + count)
            else:
                first_letter = chr(ord('A') + (count // 26) - 1)
                second_letter = chr(ord('A') + (count % 26))
                next_letter = first_letter + second_letter

            self.callsign = f"{class_code}{next_letter}"
    status = fields.Selection(
        selection=[
            ('enrolled', 'Enrolled'),
            ('active', 'Active'),
            ('graduated', 'Graduated'),
            ('dropped', 'Dropped'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='enrolled',
        required=True,
        tracking=True,
    )

    def _prepare_requirement_commands(self, class_type):
        """Prepare enrollment hour and OR-group snapshot commands from a class type."""
        hour_commands = [(5, 0, 0)]
        group_commands = [(5, 0, 0)]
        if not class_type:
            return hour_commands, group_commands

        activity_values = {}
        standalone_requirements = class_type.hour_requirement_ids.filtered(
            lambda requirement: not requirement.requirement_group_id
        )
        for requirement in standalone_requirements:
            activity_values[requirement.activity_id.id] = {
                'activity_id': requirement.activity_id.id,
                'hours_logged': 0.0,
                'is_extra': False,
                'minimum_hours': requirement.minimum_hours,
                'class_type_hour_id': requirement.id,
                'requirement_role': 'standalone',
            }

        for requirement_group in class_type.hour_requirement_group_ids:
            alternatives = requirement_group.hour_requirement_ids.filtered(
                lambda requirement: requirement.activity_id
            )
            alternative_activity_ids = alternatives.mapped('activity_id').ids
            if not alternative_activity_ids:
                continue

            group_commands.append((0, 0, {
                'source_group_id': requirement_group.id,
                'requirement_group_key': f'class_type_hours_group_{requirement_group.id}',
                'name': requirement_group.name,
                'sequence': requirement_group.sequence,
                'minimum_hours': requirement_group.minimum_hours,
                'count_as': requirement_group.count_as,
                'alternative_activity_ids': [(6, 0, alternative_activity_ids)],
            }))
            for requirement in alternatives:
                activity_values.setdefault(requirement.activity_id.id, {
                    'activity_id': requirement.activity_id.id,
                    'hours_logged': 0.0,
                    'is_extra': False,
                    'minimum_hours': 0.0,
                    'class_type_hour_id': requirement.id,
                    'requirement_role': 'alternative',
                })

        hour_commands.extend(
            (0, 0, activity_values[activity_id])
            for activity_id in sorted(activity_values)
        )
        return hour_commands, group_commands

    @api.onchange('training_class_id')
    def _onchange_training_class_id_set_status(self):
        """Set enrollment status based on class status and populate hour requirements.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.training_class_id:
            class_rec = self.training_class_id
            class_status = class_rec.status  # type: ignore

            if class_status == 'in_progress':
                self.status = 'active'
            elif class_status == 'draft':
                self.status = 'enrolled'

            class_type = class_rec.class_type_id  # type: ignore
            hour_commands, group_commands = self._prepare_requirement_commands(class_type)
            self.required_hour_ids = hour_commands  # type: ignore
            self.requirement_group_ids = group_commands  # type: ignore
            self.total_hours = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """Final safety net: Populate flight hours if the UI failed to do so.

        Args:
            vals_list: List of value dictionaries passed to the multi-record create method.

        Returns:
            models.Model: Odoo recordset returned by the ORM.
        """
        for vals in vals_list:
            # We check if the required_hour_ids commands sent by the UI are valid.
            hour_commands = vals.get('required_hour_ids', [])
            is_valid = False
            if hour_commands:
                for cmd in hour_commands:
                    if isinstance(cmd, (list, tuple)) and cmd[0] == 0:
                        if cmd[2] and cmd[2].get('activity_id'):
                            is_valid = True
                            break

            if vals.get('training_class_id'):
                training_class = self.env['fs.training.class'].browse(vals['training_class_id'])
                class_type = training_class.class_type_id  # type: ignore
                hour_commands, group_commands = self._prepare_requirement_commands(class_type)
                if not is_valid:
                    vals['required_hour_ids'] = hour_commands
                if not vals.get('requirement_group_ids') and class_type.hour_requirement_group_ids:
                    vals['requirement_group_ids'] = group_commands
        return super().create(vals_list)

    @api.onchange('required_hour_ids', 'extra_hour_ids')
    def _onchange_hours_recompute_totals(self):
        """Force real-time recalculation of total hours and progress in the UI.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        total = sum(self.required_hour_ids.mapped('hours_logged')) + \
            sum(self.extra_hour_ids.mapped('hours_logged'))
        self.total_hours = total

        progress_values = self._get_requirement_progress_values()
        self.progression = progress_values['progression']

    is_active = fields.Boolean(
        string='Is Active',
        compute='_compute_is_active',
        store=True,
    )

    # === Date Tracking ===
    enrollment_date = fields.Date(
        string='Enrollment Date',
        related='training_class_id.start_date',
        store=True,
        help="Date when the student was enrolled (class start date).",
    )
    graduation_date = fields.Date(
        string='Graduation Date',
        tracking=True,
        help="Date when the student graduated.",
    )
    drop_date = fields.Date(
        string='Drop Date',
        tracking=True,
        help="Date when the student was dropped.",
    )
    required_hour_ids = fields.One2many(
        comodel_name='fs.enrollment.hours',
        inverse_name='enrollment_id',
        string='Required Hours',
        domain=[('is_extra', '=', False)],
    )
    extra_hour_ids = fields.One2many(
        comodel_name='fs.enrollment.hours',
        inverse_name='enrollment_id',
        string='Extra Hours',
        domain=[('is_extra', '=', True)],
    )
    requirement_group_ids = fields.One2many(
        comodel_name='fs.enrollment.hours.group',
        inverse_name='enrollment_id',
        string='Alternative Requirement Groups',
        help='Snapshot of OR hour requirements generated when this enrollment was created.',
    )

    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_total_hours',
        store=True,
    )

    progression = fields.Float(
        string='Progression (%)',
        compute='_compute_progression',
        store=True,
        aggregator='avg',
        help="Percentage of minimum hours completed.",
    )
    notes = fields.Text(
        string='Notes',
    )

    # Related fields for display
    class_status = fields.Selection(
        string='Class Status',
        related='training_class_id.status',
        store=True,
    )
    student_name = fields.Char(
        string='Student Name',
        compute='_compute_personnel_fields',
        store=True,
    )
    medical_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Info'),
        ],
        compute='_compute_personnel_fields',
        string='Medical Status',
        store=True,
    )
    license_expiry_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Info'),
        ],
        compute='_compute_personnel_fields',
        string='License Status',
        store=True,
    )
    security_clearance_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Info'),
        ],
        compute='_compute_personnel_fields',
        string='Security Status',
        store=True,
    )
    insurance_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Info'),
        ],
        compute='_compute_personnel_fields',
        string='Insurance Status',
        store=True,
    )
    student_image = fields.Image(
        compute='_compute_personnel_fields',
        string='Student Image',
        store=True,
    )
    student_phone = fields.Char(
        compute='_compute_personnel_fields',
        string='Phone',
        store=True,
    )
    has_expired_status = fields.Boolean(
        compute='_compute_personnel_fields',
        string='Has Expired Status',
        store=True,
    )

    @api.depends(
        'student_id.name', 'pilot_id.name', 'enrolled_instructor_id.name',
        'student_id.medical_status', 'pilot_id.medical_status', 'enrolled_instructor_id.medical_status',
        'student_id.license_expiry_status',
        'pilot_id.qualification_ids.expiry_status', 'enrolled_instructor_id.qualification_ids.expiry_status',
        'student_id.security_clearance_status', 'pilot_id.security_clearance_status',
        'student_id.insurance_status', 'pilot_id.insurance_status',
        'student_id.image_128', 'pilot_id.image_128', 'enrolled_instructor_id.image_128',
        'student_id.phone', 'pilot_id.phone', 'enrolled_instructor_id.phone',
        'student_id.has_expired_status', 'pilot_id.has_expired_qualification'
    )
    def _compute_personnel_fields(self):
        """Compute personnel fields values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            person = record.student_id or record.pilot_id or record.enrolled_instructor_id
            if person:
                record.student_name = person.name or False  # type: ignore[attr-defined]
                record.medical_status = getattr(person, 'medical_status', 'no_expiry') or 'no_expiry'

                # License status
                if hasattr(person, 'license_expiry_status'):
                    record.license_expiry_status = getattr(person, 'license_expiry_status', 'no_expiry') or 'no_expiry'
                elif hasattr(person, 'qualification_ids'):
                    # Pilots/Instructors have qualifications instead of a single license status
                    statuses = person.qualification_ids.mapped('expiry_status')  # type: ignore
                    if 'expired' in statuses:
                        record.license_expiry_status = 'expired'
                    elif 'expiring' in statuses:
                        record.license_expiry_status = 'expiring'
                    elif 'valid' in statuses:
                        record.license_expiry_status = 'valid'
                    else:
                        record.license_expiry_status = 'no_expiry'
                else:
                    record.license_expiry_status = 'no_expiry'

                record.security_clearance_status = getattr(
                    person, 'security_clearance_status', 'no_expiry') or 'no_expiry'
                record.insurance_status = getattr(person, 'insurance_status', 'no_expiry') or 'no_expiry'
                record.student_image = getattr(person, 'image_128', False)
                record.student_phone = getattr(person, 'phone', False)

                # Overall expired status
                if hasattr(person, 'has_expired_status'):
                    record.has_expired_status = getattr(person, 'has_expired_status', False)
                elif hasattr(person, 'has_expired_qualification'):
                    # Pilot
                    has_exp = (
                        getattr(person, 'has_expired_qualification', False) or
                        getattr(person, 'medical_status', False) == 'expired' or
                        getattr(person, 'security_clearance_status', False) == 'expired' or
                        getattr(person, 'insurance_status', False) == 'expired'
                    )
                    record.has_expired_status = has_exp
                else:
                    # Generic compute
                    record.has_expired_status = (
                        record.medical_status == 'expired' or
                        record.license_expiry_status == 'expired' or
                        record.security_clearance_status == 'expired' or
                        record.insurance_status == 'expired'
                    )
            else:
                record.student_name = False
                record.medical_status = 'no_expiry'
                record.license_expiry_status = 'no_expiry'
                record.security_clearance_status = 'no_expiry'
                record.insurance_status = 'no_expiry'
                record.student_image = False
                record.student_phone = False
                record.has_expired_status = False
    remaining_hours = fields.Float(
        string='Remaining Syllabus Hours',
        compute='_compute_remaining_hours',
        help="Total hours remaining to complete the mandatory syllabus requirements.",
    )
    remaining_breakdown_html = fields.Html(
        string='Remaining Breakdown',
        compute='_compute_remaining_breakdown_html',
    )

    @api.depends('status')
    def _compute_is_active(self):
        """Compute is active values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.is_active = record.status == 'active'

    @api.depends('required_hour_ids.hours_logged', 'extra_hour_ids.hours_logged')
    def _compute_total_hours(self):
        """Compute total hours from all hour records (required + extra).

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.total_hours = sum(record.required_hour_ids.mapped('hours_logged')) + \
                sum(record.extra_hour_ids.mapped('hours_logged'))

    def _get_requirement_progress_values(self):
        """Return OR-aware syllabus progress values for a single enrollment."""
        self.ensure_one()
        total_required = 0.0
        total_progress = 0.0
        remaining = 0.0
        breakdown_items = []

        standalone_requirements = self.required_hour_ids.filtered(
            lambda hour: not hour.is_extra and hour.minimum_hours > 0.0
        )
        for requirement in standalone_requirements:
            required_hours = requirement.minimum_hours
            logged_hours = requirement.hours_logged
            completed_hours = min(logged_hours, required_hours)
            remaining_hours = max(0.0, required_hours - logged_hours)

            total_required += required_hours
            total_progress += completed_hours
            remaining += remaining_hours
            if remaining_hours > 0.0:
                progress = (completed_hours / required_hours) * 100.0 if required_hours else 0.0
                breakdown_items.append({
                    'name': requirement.activity_id.display_name,
                    'remaining_hours': remaining_hours,
                    'progress': progress,
                    'is_group': False,
                })

        for requirement_group in self.requirement_group_ids:
            required_hours = requirement_group.minimum_hours
            if required_hours <= 0.0:
                continue

            logged_hours = requirement_group._get_logged_hours()
            completed_hours = min(logged_hours, required_hours)
            remaining_hours = max(0.0, required_hours - logged_hours)

            total_required += required_hours
            total_progress += completed_hours
            remaining += remaining_hours
            if remaining_hours > 0.0:
                progress = (completed_hours / required_hours) * 100.0
                breakdown_items.append({
                    'name': requirement_group.name,
                    'remaining_hours': remaining_hours,
                    'progress': progress,
                    'is_group': True,
                    'activities': requirement_group.alternative_activity_names,
                })

        if total_required > 0.0:
            progression = (total_progress / total_required) * 100.0
        else:
            progression = 100.0 if self.total_hours > 0.0 else 0.0

        return {
            'total_required': total_required,
            'total_progress': total_progress,
            'remaining': remaining,
            'progression': progression,
            'breakdown_items': breakdown_items,
        }

    @staticmethod
    def _format_hours_for_display(hours):
        """Format decimal hours similarly to Odoo's float_time widget."""
        hours_value, minutes_value = divmod(abs(hours) * 60, 60)
        return f"{int(hours_value)}:{int(minutes_value):02d}"

    @api.depends(
        'required_hour_ids.hours_logged',
        'required_hour_ids.minimum_hours',
        'required_hour_ids.activity_id',
        'extra_hour_ids.hours_logged',
        'extra_hour_ids.activity_id',
        'requirement_group_ids.minimum_hours',
        'requirement_group_ids.alternative_activity_ids',
    )
    def _compute_progression(self):
        """Compute progression values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.progression = record._get_requirement_progress_values()['progression']

    @api.depends(
        'required_hour_ids.hours_logged',
        'required_hour_ids.minimum_hours',
        'extra_hour_ids.hours_logged',
        'extra_hour_ids.activity_id',
        'requirement_group_ids.minimum_hours',
        'requirement_group_ids.alternative_activity_ids',
    )
    def _compute_remaining_hours(self):
        """Calculate the sum of hours still required for mandatory activities.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.remaining_hours = record._get_requirement_progress_values()['remaining']

    @api.depends(
        'required_hour_ids.hours_logged',
        'required_hour_ids.minimum_hours',
        'required_hour_ids.activity_id',
        'extra_hour_ids.hours_logged',
        'extra_hour_ids.activity_id',
        'requirement_group_ids.name',
        'requirement_group_ids.minimum_hours',
        'requirement_group_ids.alternative_activity_ids',
    )
    def _compute_remaining_breakdown_html(self):
        """Generate a pretty HTML summary of remaining hours per activity.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            breakdown_items = record._get_requirement_progress_values()['breakdown_items']
            if not breakdown_items:
                record.remaining_breakdown_html = '<span class="text-success small"><i class="fa fa-check-circle"/> Syllabus Fully Completed</span>'
                continue

            breakdown_items = sorted(
                breakdown_items,
                key=lambda item: item['remaining_hours'],
                reverse=True,
            )

            html = '<div class="d-flex flex-column gap-1">'
            for item in breakdown_items[:3]:
                rem_h_fmt = self._format_hours_for_display(item['remaining_hours'])
                progress = item['progress']
                color = "text-danger" if progress < 50 else "text-warning"
                if item['is_group']:
                    item_name = f"{item['name']}: {item.get('activities') or ''}"
                else:
                    item_name = item['name']

                html += f'''
                    <div class="d-flex justify-content-between align-items-center small" style="min-width: 220px;">
                        <span class="text-muted text-truncate me-2" style="max-width: 170px;" title="{item_name}">{item_name}</span>
                        <strong class="{color}">{rem_h_fmt} left</strong>
                    </div>
                '''

            if len(breakdown_items) > 3:
                html += f'<div class="text-muted x-small italic text-center text-decoration-underline mt-1">+{len(breakdown_items)-3} more activities...</div>'

            html += '</div>'
            record.remaining_breakdown_html = html

    @api.constrains('student_id', 'pilot_id', 'enrolled_instructor_id', 'training_class_id', 'for_licensed_personnel')
    def _check_enrolled_person_type(self):
        """Enforce mutual exclusivity: students for regular classes, pilots/instructors for licensed-personnel classes.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.

        Raises:
            ValidationError: If record data violates a model constraint.
        """
        for record in self:
            is_licensed = record.for_licensed_personnel
            has_student = bool(record.student_id)
            has_pilot = bool(record.pilot_id)
            has_instr = bool(record.enrolled_instructor_id)

            if is_licensed:
                # Licensed class: pilot OR instructor required; student forbidden
                if has_student:
                    raise ValidationError(
                        "This class is for licensed personnel only. "
                        "Please select a Pilot or Instructor instead of a Student."
                    )
                if not has_pilot and not has_instr:
                    raise ValidationError(
                        "Please select a Pilot or an Instructor for this licensed-personnel class."
                    )
            else:
                # Regular class: student required; pilot/instructor forbidden
                if has_pilot or has_instr:
                    raise ValidationError(
                        "This class is for students only. "
                        "Please select a Student instead of a Pilot or Instructor."
                    )
                if not has_student:
                    raise ValidationError(
                        "Please select a Student for this enrollment."
                    )

    @api.constrains('student_id', 'pilot_id', 'enrolled_instructor_id', 'training_class_id')
    def _check_unique_person_per_class(self):
        """Prevent duplicate enrollments for any supported person type in the same class.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.

        Raises:
            ValidationError: If record data violates a model constraint.
        """
        for record in self:
            if not record.training_class_id:
                continue
            person_field = False
            person = False
            if record.student_id:
                person_field = 'student_id'
                person = record.student_id
            elif record.pilot_id:
                person_field = 'pilot_id'
                person = record.pilot_id
            elif record.enrolled_instructor_id:
                person_field = 'enrolled_instructor_id'
                person = record.enrolled_instructor_id
            if not person_field or not person:
                continue
            duplicate = self.search([
                ('training_class_id', '=', record.training_class_id.id),
                (person_field, '=', person.id),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    "%(person)s is already enrolled in class %(class_name)s."
                ) % {
                    'person': person.display_name,
                    'class_name': record.training_class_id.display_name,
                })

    @api.constrains('student_id', 'pilot_id', 'enrolled_instructor_id', 'status')
    def _check_one_active_enrollment(self):
        """Ensure each person has only one active enrollment at a time.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.

        Raises:
            ValidationError: If record data violates a model constraint.
        """
        for record in self:
            if record.status == 'active':
                if record.student_id:
                    other_active = self.search([
                        ('student_id', '=', record.student_id.id),
                        ('status', '=', 'active'),
                        ('id', '!=', record.id),
                    ])
                    if other_active:
                        raise ValidationError(
                            f"Student '{record.student_id.display_name}' already has an active enrollment "
                            f"in class '{other_active[0].training_class_id.display_name}'."
                        )
                if record.pilot_id:
                    other_active = self.search([
                        ('pilot_id', '=', record.pilot_id.id),
                        ('status', '=', 'active'),
                        ('id', '!=', record.id),
                    ])
                    if other_active:
                        raise ValidationError(
                            f"Pilot '{record.pilot_id.display_name}' already has an active enrollment "
                            f"in class '{other_active[0].training_class_id.display_name}'."
                        )
                if record.enrolled_instructor_id:
                    other_active = self.search([
                        ('enrolled_instructor_id', '=', record.enrolled_instructor_id.id),
                        ('status', '=', 'active'),
                        ('id', '!=', record.id),
                    ])
                    if other_active:
                        raise ValidationError(
                            f"Instructor '{record.enrolled_instructor_id.display_name}' already has an active enrollment "
                            f"in class '{other_active[0].training_class_id.display_name}'."
                        )

    def action_graduate(self):
        """Mark enrollment as graduated. Checks for 100% completion.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.

        Raises:
            UserError: If user-facing business validation fails.
        """
        today = fields.Date.context_today(self)
        for record in self:
            if record.progression < 100.0:
                person_name = record.enrolled_person_name or record.display_name
                raise UserError(
                    f"'{person_name}' cannot graduate yet. "
                    f"Syllabus completion is only {record.progression:.1f}%."
                )
            if record.status in ('enrolled', 'active'):
                record.status = 'graduated'
                record.graduation_date = today

    def action_drop(self):
        """Mark enrollment as dropped.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        today = fields.Date.context_today(self)
        for record in self:
            if record.status in ('enrolled', 'active'):
                record.status = 'dropped'
                record.drop_date = today

    def action_reinstate(self):
        """Reinstate a dropped or graduated student back to appropriate status.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        for record in self:
            if record.status in ('dropped', 'graduated'):
                # Set status based on class status
                class_status = record.training_class_id.status  # type: ignore
                if class_status == 'in_progress':
                    record.status = 'active'
                elif class_status == 'draft':
                    record.status = 'enrolled'
                else:
                    # For completed/cancelled classes, set to enrolled
                    record.status = 'enrolled'
                # Clear relevant dates
                record.drop_date = False
                record.graduation_date = False

    def action_view_student(self):
        """Open the enrolled person's form view.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.

        Raises:
            UserError: If user-facing business validation fails.
        """
        self.ensure_one()
        if self.student_id:
            res_model = 'fs.student'
            res_id = self.student_id.id
        elif self.pilot_id:
            res_model = 'fs.pilot'
            res_id = self.pilot_id.id
        elif self.enrolled_instructor_id:
            res_model = 'fs.instructor'
            res_id = self.enrolled_instructor_id.id
        else:
            raise UserError(_("This enrollment is not linked to a person."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': res_model,
            'res_id': res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_enrollment(self):
        """Open the enrollment form in a popup window.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Student Enrollment',
            'res_model': 'fs.student.enrollment',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class FsEnrollmentHoursGroup(models.Model):
    """Enrollment-level snapshot of an OR hour requirement group."""

    _name = 'fs.enrollment.hours.group'
    _description = 'Enrollment Alternative Hour Requirement Group'
    _order = 'enrollment_id, sequence, name'

    enrollment_id = fields.Many2one(
        comodel_name='fs.student.enrollment',
        string='Enrollment',
        required=True,
        ondelete='cascade',
    )
    source_group_id = fields.Many2one(
        comodel_name='fs.class.type.hours.group',
        string='Source Class Type Group',
        ondelete='set null',
        readonly=True,
    )
    requirement_group_key = fields.Char(
        string='Requirement Group Key',
        required=True,
        readonly=True,
        help='Stable snapshot key used to evaluate this enrollment independently of template changes.',
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    minimum_hours = fields.Float(
        string='Required Hours',
        required=True,
        default=0.0,
    )
    count_as = fields.Selection(
        selection=ENROLLMENT_REQUIREMENT_GROUP_COUNT_AS_SELECTION,
        string='Count As',
        required=True,
        default='unallocated',
    )
    alternative_activity_ids = fields.Many2many(
        comodel_name='fs.flight.activity',
        relation='fs_enrollment_hours_group_activity_rel',
        column1='group_id',
        column2='activity_id',
        string='Alternative Activities',
    )
    alternative_activity_names = fields.Char(
        string='Alternative Activity Names',
        compute='_compute_alternative_activity_names',
    )
    logged_hours = fields.Float(
        string='Logged Hours',
        compute='_compute_progress_fields',
    )
    remaining_hours = fields.Float(
        string='Remaining',
        compute='_compute_progress_fields',
    )
    progress_percentage = fields.Float(
        string='Progress',
        compute='_compute_progress_fields',
    )

    _unique_group_key = models.Constraint(
        'UNIQUE(enrollment_id, requirement_group_key)',
        'This alternative requirement group already exists for this enrollment.',
    )

    @api.depends('alternative_activity_ids.name')
    def _compute_alternative_activity_names(self):
        """Display alternative activity names in list views."""
        for record in self:
            record.alternative_activity_names = ' / '.join(
                record.alternative_activity_ids.mapped('display_name')
            )

    def _get_logged_hours(self):
        """Return required and extra logged hours matching this group's alternatives."""
        self.ensure_one()
        activity_ids = set(self.alternative_activity_ids.ids)
        if not activity_ids or not self.enrollment_id:
            return 0.0

        matching_required_hours = self.enrollment_id.required_hour_ids.filtered(
            lambda hour: hour.activity_id.id in activity_ids
        )
        matching_extra_hours = self.enrollment_id.extra_hour_ids.filtered(
            lambda hour: hour.activity_id.id in activity_ids
        )
        return sum(matching_required_hours.mapped('hours_logged')) + \
            sum(matching_extra_hours.mapped('hours_logged'))

    @api.depends(
        'minimum_hours',
        'alternative_activity_ids',
        'enrollment_id.required_hour_ids.hours_logged',
        'enrollment_id.required_hour_ids.activity_id',
        'enrollment_id.extra_hour_ids.hours_logged',
        'enrollment_id.extra_hour_ids.activity_id',
    )
    def _compute_progress_fields(self):
        """Compute OR-group logged, remaining, and percentage values."""
        for record in self:
            logged_hours = record._get_logged_hours()
            record.logged_hours = logged_hours
            record.remaining_hours = max(0.0, record.minimum_hours - logged_hours)
            if record.minimum_hours > 0.0:
                record.progress_percentage = min(
                    (logged_hours / record.minimum_hours) * 100.0,
                    100.0,
                )
            else:
                record.progress_percentage = 0.0

    @api.constrains('minimum_hours')
    def _check_minimum_hours(self):
        """Require positive snapshot group hours."""
        for record in self:
            if record.minimum_hours <= 0.0:
                raise ValidationError('Alternative requirement groups must require positive hours.')

    @api.constrains('alternative_activity_ids')
    def _check_alternative_count(self):
        """Require at least two alternatives in every enrollment OR group."""
        for record in self:
            if len(record.alternative_activity_ids) < 2:
                raise ValidationError(
                    'Alternative requirement groups must contain at least two activities.'
                )


class FsEnrollmentHours(models.Model):
    """Flight hours logged per activity for an enrollment.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.enrollment.hours``.
        _description (str): Human-readable model label, ``Enrollment Flight Hours``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

    _name = 'fs.enrollment.hours'
    _description = 'Enrollment Flight Hours'
    _order = 'activity_id'

    enrollment_id = fields.Many2one(
        comodel_name='fs.student.enrollment',
        string='Enrollment',
        required=True,
        ondelete='cascade',
    )
    is_extra = fields.Boolean(
        string='Extra Hours',
        default=False,
        help="True if these are extra hours added specifically for this student.",
    )
    class_type_hour_id = fields.Many2one(
        comodel_name='fs.class.type.hours',
        string='Class Type Requirement',
        ondelete='set null',
        readonly=True,
    )
    requirement_role = fields.Selection(
        selection=ENROLLMENT_REQUIREMENT_ROLE_SELECTION,
        string='Requirement Type',
        default='standalone',
        required=True,
        help='Identifies standalone requirements and activities accepted by OR groups.',
    )
    activity_id = fields.Many2one(
        comodel_name='fs.flight.activity',
        string='Activity',
        required=True,
        ondelete='restrict',
    )
    discipline_id = fields.Many2one(
        comodel_name='fs.flight.discipline',
        related='activity_id.discipline_id',
        store=True,
    )
    discipline_code = fields.Char(
        string='Discipline Code',
        related='discipline_id.code',
    )
    flight_type_id = fields.Many2one(
        comodel_name='fs.flight.type',
        related='activity_id.flight_type_id',
        store=True,
    )
    flight_type_code = fields.Char(
        string='Type Code',
        related='flight_type_id.code',
    )
    minimum_hours = fields.Float(
        string='Required Hours',
        default=0.0,
        help='Snapshot of standalone required hours at enrollment creation time.',
    )
    hours_logged = fields.Float(
        string='Hours Logged',
        default=0.0,
    )
    progress_percentage = fields.Float(
        string='Progress',
        compute='_compute_progress_percentage',
        store=True,
    )
    remaining_hours = fields.Float(
        string='Remaining',
        compute='_compute_remaining_hours_line',
    )
    requirement_group_names = fields.Char(
        string='OR Groups',
        compute='_compute_requirement_group_names',
        help='Alternative requirement groups that accept this activity.',
    )

    @api.depends(
        'activity_id',
        'enrollment_id.requirement_group_ids.name',
        'enrollment_id.requirement_group_ids.alternative_activity_ids',
    )
    def _compute_requirement_group_names(self):
        """Show the OR groups that accept this activity."""
        for record in self:
            if not record.enrollment_id or not record.activity_id:
                record.requirement_group_names = False
                continue

            matching_groups = record.enrollment_id.requirement_group_ids.filtered(
                lambda group: record.activity_id in group.alternative_activity_ids
            )
            record.requirement_group_names = ' / '.join(matching_groups.mapped('name'))

    @api.depends('hours_logged', 'minimum_hours')
    def _compute_remaining_hours_line(self):
        """Calculate remaining hours for this specific activity.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.remaining_hours = max(0.0, record.minimum_hours - record.hours_logged)

    @api.depends('hours_logged', 'minimum_hours')
    def _compute_progress_percentage(self):
        """Compute progress percentage for this hour requirement.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            if record.minimum_hours > 0:
                record.progress_percentage = min(
                    (record.hours_logged / record.minimum_hours) * 100.0,
                    100.0,
                )
            else:
                record.progress_percentage = 0.0

    _unique_activity = models.Constraint(
        'UNIQUE(enrollment_id, activity_id, is_extra)',
        'This activity already exists in this section (Mandatory or Additional).',
    )
