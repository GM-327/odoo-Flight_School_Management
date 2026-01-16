# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import timedelta, datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FsSchedulingWizard(models.TransientModel):
    """Multi-step wizard for batch scheduling of flight missions."""

    _name = 'fs.scheduling.wizard'
    _description = 'Scheduling Wizard'

    # === Display Name for Title ===
    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('date', 'state')
    def _compute_display_name(self):
        state_labels = {'step1': 'Selection', 'step2': 'Review & Reorder', 'step3': 'Confirm'}
        for wizard in self:
            date_str = wizard.date.strftime('%d/%m/%Y') if wizard.date else 'New'
            state_label = state_labels.get(wizard.state or 'step1', 'Selection')
            wizard.display_name = f"Schedule for {date_str} - {state_label}"

    # === Step Management ===
    state = fields.Selection([
        ('step1', 'Selection'),
        ('step2', 'Review & Reorder'),
        ('step3', 'Confirm'),
    ], string='Step', default='step1', required=True)

    # === Step 1: Basic Parameters ===
    def _default_date(self):
        today = fields.Date.context_today(self)
        next_day = today + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        return next_day

    date = fields.Date(
        string='Scheduling Date',
        required=True,
        default=_default_date,
    )
    callsign_prefix = fields.Char(
        string='Callsign Prefix',
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param('flight_school.mission_callsign_prefix', 'ABS'),  # type: ignore
    )
    next_callsign_number = fields.Integer(
        string='First Flight Number',
        default=lambda self: self._default_next_callsign_number(),
    )
    first_start_time = fields.Float(
        string='First Mission Start Time',
        default=7.0,
        help="Start time for the first mission (e.g., 7.0 = 07:00).",
    )
    last_end_time = fields.Float(
        string='Last Mission End Time',
        default=15.75,  # 15:45
        help="All missions must end before this time (e.g., 15.75 = 15:45).",
    )
    
    # Many2many for step 1 selection
    selected_enrollment_ids = fields.Many2many(
        comodel_name='fs.student.enrollment',
        relation='fs_scheduling_wizard_enrollment_rel',
        column1='wizard_id',
        column2='enrollment_id',
        string='Selected Students',
        domain="[('status', '=', 'active'), ('progression', '<', 100.0)]",
    )
    selected_instructor_ids = fields.Many2many(
        comodel_name='fs.instructor',
        relation='fs_scheduling_wizard_instructor_rel',
        column1='wizard_id',
        column2='instructor_id',
        string='Available Instructors',
        domain="[('active', '=', True)]",
    )
    
    # === Step 2 & 3: Generated Lines ===
    line_ids = fields.One2many(
        comodel_name='fs.scheduling.wizard.line',
        inverse_name='wizard_id',
        string='Scheduling Lines',
    )

    # === Computed Counts for UI ===
    selected_count = fields.Integer(
        string='Selected Flights',
        compute='_compute_counts',
    )
    total_count = fields.Integer(
        string='Total Flights',
        compute='_compute_counts',
    )

    @api.depends('line_ids')
    def _compute_counts(self):
        for wizard in self:
            wizard.total_count = len(wizard.line_ids)
            wizard.selected_count = len(wizard.line_ids)  # All lines are selected (delete to remove)

    def _default_next_callsign_number(self):
        """Get next aircraft callsign number based on existing flights for the current year."""
        prefix = self.env['ir.config_parameter'].sudo().get_param('flight_school.mission_callsign_prefix', 'ABS')  # type: ignore
        # Get current year for filtering
        today = fields.Date.context_today(self)
        year_start = today.replace(month=1, day=1)
        year_end = today.replace(month=12, day=31)
        
        last = self.env['fs.scheduled.flight'].search([
            ('callsign', '=like', f'{prefix}%'),
            ('date', '>=', year_start),
            ('date', '<=', year_end),
        ], order='callsign desc', limit=1)
        
        if last and last.callsign and last.callsign[len(prefix):].isdigit():  # type: ignore
            return int(last.callsign[len(prefix):]) + 1  # type: ignore
        return 1

    def _get_next_sim_callsign_number(self):
        """Get next simulator callsign number based on existing SIM flights for the current year."""
        # Get current year for filtering
        today = fields.Date.context_today(self)
        year_start = today.replace(month=1, day=1)
        year_end = today.replace(month=12, day=31)
        
        last = self.env['fs.scheduled.flight'].search([
            ('callsign', '=like', 'SIM%'),
            ('date', '>=', year_start),
            ('date', '<=', year_end),
        ], order='callsign desc', limit=1)
        
        if last and last.callsign and last.callsign[3:].isdigit():  # type: ignore
            return int(last.callsign[3:]) + 1  # type: ignore
        return 1

    # === Step Navigation ===
    def action_next_step(self):
        """Move to next step."""
        self.ensure_one()
        if self.state == 'step1':
            self._generate_schedule_lines()
            self.state = 'step2'
        elif self.state == 'step2':
            self._validate_before_confirm()
            self._assign_schedule_details()
            self.state = 'step3'
        return self._reopen_wizard()

    def action_previous_step(self):
        """Move to previous step."""
        self.ensure_one()
        if self.state == 'step2':
            self.state = 'step1'
        elif self.state == 'step3':
            self.state = 'step2'
        return self._reopen_wizard()

    def action_add_mission(self):
        """Open a form view to add a new mission (wizard line) for scheduling."""
        self.ensure_one()
        # Get max sequence for new line
        max_seq = max(self.line_ids.mapped('sequence'), default=0) + 1
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add New Mission'),
            'res_model': 'fs.scheduling.wizard.line',
            'view_mode': 'form',
            'view_id': self.env.ref('fs_scheduling.view_fs_scheduling_wizard_line_form').id,
            'target': 'new',
            'context': {
                'default_wizard_id': self.id,
                'default_sequence': max_seq,
                'default_is_added_mission': True,
                'form_view_initial_mode': 'edit',
            },
        }

    def _reopen_wizard(self):
        """Reopen the wizard to refresh the view."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # === Step 1 -> Step 2: Generate Lines ===
    def _generate_schedule_lines(self):
        """Generate scheduling lines based on selected students and instructors.
        Times and aircraft are NOT assigned here - they are assigned in Step 4."""
        if not self.selected_enrollment_ids:
            raise UserError(_("Please select at least one student to schedule."))
        
        if not self.selected_instructor_ids:
            raise UserError(_("Please select at least one available instructor."))

        # Clear existing lines
        self.line_ids.unlink()

        available_instructor_ids = self.selected_instructor_ids.ids
        
        lines = []
        for enrollment in self.selected_enrollment_ids:
            class_rec = enrollment.training_class_id  # type: ignore
            class_type = class_rec.class_type_id if class_rec else False
            default_instructor = enrollment.instructor_id  # type: ignore
            
            # Find an available instructor from selected ones
            instructor = False
            if default_instructor and default_instructor.id in available_instructor_ids:
                if not default_instructor.has_expired_qualification:  # type: ignore
                    instructor = default_instructor
            
            # If default instructor not available, find another
            if not instructor:
                for inst_id in available_instructor_ids:
                    inst = self.env['fs.instructor'].browse(inst_id)
                    if not inst.has_expired_qualification:  # type: ignore
                        instructor = inst
                        break
            
            # Mission suggestion
            mission = False
            duration = 1.0
            is_solo = False
            is_exam = False
            if class_type and class_type.flight_mission_ids:
                mission = class_type.flight_mission_ids.filtered(
                    lambda m: not m.is_extra
                )[:1]
                if mission:
                    duration = mission.duration_hours or 1.0
                    is_exam = mission.is_exam
                    if mission.flight_type_id and mission.flight_type_id.is_solo:
                        is_solo = True
            
            # Check examinator qualification
            has_examinator_qual = False
            if instructor and is_exam:
                has_examinator_qual = any(
                    q.qualification_id.is_examinator 
                    for q in instructor.qualification_ids  # type: ignore
                    if q.qualification_id
                )
            
            # Determine aircraft types: use student's assigned type (if non-simulator) or class types
            assigned_type = enrollment.aircraft_type_id  # type: ignore
            if assigned_type and not assigned_type.is_simulator:  # type: ignore
                aircraft_type_ids = [(6, 0, [assigned_type.id])]
            elif class_rec and class_rec.aircraft_type_ids:
                aircraft_type_ids = [(6, 0, class_rec.aircraft_type_ids.ids)]
            else:
                aircraft_type_ids = False
            # Find crew member IDs for the enrollment and instructor
            # Student enrollment uses enrollment ID directly as crew member ID
            pilot1_crew_id = enrollment.id  # enrollment ID is used directly as crew member ID for students
            
            # Find instructor's crew member ID (instructor ID + 1000000 offset)
            pilot2_crew_id = False
            if instructor:
                instructor_crew = self.env['fs.crew.member'].search([
                    ('source_model', '=', 'fs.instructor'),
                    ('source_id', '=', instructor.id)
                ], limit=1)
                pilot2_crew_id = instructor_crew.id if instructor_crew else False
            
            lines.append((0, 0, {
                'sequence': len(lines) + 1,
                'callsign_number': 0,  # Will be assigned in Step 3
                'flight_category': 'student_training',
                'pilot1_crew_id': pilot1_crew_id,
                'pilot1_function': 'solo' if is_solo else 'student',
                'pilot2_crew_id': pilot2_crew_id,
                'pilot2_function': 'supervisor' if is_solo else 'instructor',
                'training_class_code': class_rec.code if class_rec else '',
                'class_type_id': class_type.id if class_type else False,
                'aircraft_type_ids': aircraft_type_ids,
                'aircraft_id': False,  # Will be assigned in Step 3
                'mission_id': mission.id if mission else False,
                'duration': duration,
                'start_time': 0,  # Will be assigned in Step 3
                'has_examinator_warning': is_exam and not has_examinator_qual,
            }))
        
        # Custom sort for the initial list: Simulators at the end, then by Pilot 2 callsign/name
        def line_sort_key(l_vals):
            # l_vals is (0, 0, { ... })
            vals = l_vals[2]
            is_sim = False
            if vals.get('mission_id'):
                is_sim = self.env['fs.flight.mission'].browse(vals['mission_id']).is_sim # type: ignore
            
            pilot2_name = ''
            if vals.get('pilot2_crew_id'):
                crew = self.env['fs.crew.member'].browse(vals['pilot2_crew_id'])
                pilot2_name = crew.name or '' # type: ignore
            
            return (is_sim, pilot2_name, vals.get('sequence', 0))

        lines.sort(key=line_sort_key)
        
        # Update sequences after sorting
        for i, l_vals in enumerate(lines):
            l_vals[2]['sequence'] = i + 1
            
        self.line_ids = lines

    def _find_available_slot(self, resource_id, busy_map, min_start, duration):
        """Find the earliest available time slot for a resource."""
        if not resource_id or resource_id not in busy_map:
            return min_start
        
        busy_slots = sorted(busy_map[resource_id], key=lambda x: x[0])
        current_time = min_start
        
        for slot_start, slot_end in busy_slots:
            if current_time + duration <= slot_start:
                return current_time
            current_time = max(current_time, slot_end)
        
        return current_time

    def _is_slot_available(self, resource_id, busy_map, start_time, duration):
        """Check if a time slot is available for a resource."""
        if not resource_id or resource_id not in busy_map:
            return True
        
        end_time = start_time + duration
        for slot_start, slot_end in busy_map[resource_id]:
            if start_time < slot_end and end_time > slot_start:
                return False
        return True

    # === Step 2 -> Step 3: Validation ===
    def _validate_before_confirm(self):
        """Validate lines before assigning schedule details."""
        if not self.line_ids:
            raise UserError(_("No flights to schedule. Please go back and add students."))
        
        # Check for missing required fields and examinator qualification
        for line in self.line_ids:
            # Route is required for ALL flight types EXCEPT simulators
            if not line.route_id and not line.is_sim:  # type: ignore
                # Build descriptive info for the error message
                if line.pilot1_crew_id:  # type: ignore
                    flight_desc = line.pilot1_crew_id.display_name  # type: ignore
                elif line.pilot2_crew_id:  # type: ignore
                    flight_desc = line.pilot2_crew_id.display_name  # type: ignore
                else:
                    flight_desc = _("Line %d") % line.sequence  # type: ignore
                raise UserError(_(
                    "⚠️ Route / Area is required!\n\n"
                    "Please select a Route or Area for: %s\n\n"
                    "Go to the 'Route / Area' column in Step 2 and select an option for this flight."
                ) % flight_desc)
            
            # For student training, mission is required
            if line.flight_category == 'student_training':  # type: ignore
                if not line.pilot1_crew_id or line.pilot1_crew_id.member_type != 'student':  # type: ignore
                    raise UserError(_("Student crew member is required for student training flights (line %d).") % line.sequence)  # type: ignore
                if not line.mission_id:  # type: ignore
                    raise UserError(_("Mission is required for student: %s") % line.pilot1_crew_id.display_name)  # type: ignore
                # Only require instructor for non-solo flights
                is_solo_flight = line.pilot1_function in ('solo',)  # type: ignore
                if not line.pilot2_crew_id and not is_solo_flight:  # type: ignore
                    raise UserError(_("Instructor is required for dual flight: %s") % line.pilot1_crew_id.display_name)  # type: ignore
            
            # For staff training, require instructor/pilot and activity or custom activity
            elif line.flight_category == 'staff_training':  # type: ignore
                if not line.pilot1_crew_id:  # type: ignore
                    raise UserError(_("Pilot 1 (instructor or pilot) is required for staff training flight (line %d).") % line.sequence)  # type: ignore
                if not line.activity_id and not line.custom_activity_id:  # type: ignore
                    raise UserError(_("Flight Activity or Custom Activity is required for staff training (line %d).") % line.sequence)  # type: ignore
                if not line.aircraft_type_ids:  # type: ignore
                    raise UserError(_("Aircraft Type(s) must be selected for staff training (line %d).") % line.sequence)  # type: ignore
            
            # Check examinator qualification for exam missions or exam custom activities
            is_exam_flight = (
                (line.mission_id and line.mission_id.is_exam) or  # type: ignore
                (line.custom_activity_id and line.custom_activity_id.is_exam)  # type: ignore
            )
            if is_exam_flight and line.pilot2_crew_id and line.pilot2_crew_id.member_type == 'instructor':  # type: ignore
                # Get the actual instructor record to check qualifications
                instructor = line.pilot2_crew_id.get_source_record()  # type: ignore
                if instructor:
                    has_examinator = any(
                        q.qualification_id.is_examinator 
                        for q in instructor.qualification_ids  # type: ignore
                        if q.qualification_id
                    )
                    if not has_examinator:
                        exam_name = line.mission_id.name if line.mission_id else line.custom_activity_id.name  # type: ignore
                        raise UserError(_(
                            "Exam activity '%s' requires an instructor with examinator qualification.\n"
                            "Instructor '%s' does not have this qualification."
                        ) % (exam_name, line.pilot2_crew_id.display_name))  # type: ignore

    # === Step 2 -> Step 3: Assign Times, Aircraft, and Callsigns ===
    def _assign_schedule_details(self):
        """Assign start times, aircraft, and callsign numbers based on current line order.
        
        Aircraft flights are scheduled first, then simulator flights.
        Each group has its own callsign sequence:
        - Aircraft: Uses main callsign prefix (e.g., ABS0001)
        - Simulators: Uses SIM prefix (e.g., SIM0001)
        """
        # Sort lines: Normal Aircraft -> ADD Missions -> Simulators
        # Within each group, order by instructor callsign/name then sequence
        sorted_lines = self.line_ids.sorted(key=lambda l: (
            2 if l.is_sim else (1 if l.is_added_mission else 0), # type: ignore
            (l.pilot2_crew_id.name or '') if l.pilot2_crew_id else '', # type: ignore
            l.sequence # type: ignore
        ))  # type: ignore
        
        # Update sequence numbers to reflect the new order
        for i, line in enumerate(sorted_lines):
            line.sequence = i + 1  # type: ignore
        
        # Get existing flights for this date
        existing_flights = self.env['fs.scheduled.flight'].search([
            ('date', '=', self.date),
            ('status', '!=', 'cancelled'),
        ])
        
        # Get buffer time from config
        buffer_minutes = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.scheduling_buffer_minutes', '15'
        ))  # type: ignore
        buffer_hours = buffer_minutes / 60.0
        
        # Build occupancy maps
        instructor_busy = {}
        aircraft_busy = {}
        
        for flight in existing_flights:
            end_time = flight.start_time + flight.duration + buffer_hours  # type: ignore
            if flight.instructor_id:  # type: ignore
                instructor_busy.setdefault(flight.instructor_id.id, []).append(  # type: ignore
                    (flight.start_time, end_time)  # type: ignore
                )
            if flight.aircraft_id:  # type: ignore
                aircraft_busy.setdefault(flight.aircraft_id.id, []).append(  # type: ignore
                    (flight.start_time, end_time)  # type: ignore
                )
        
        base_start_time = self.first_start_time or 8.0
        
        # Separate callsign sequences for aircraft and simulators
        next_aircraft_callsign = self.next_callsign_number
        next_sim_callsign = self._get_next_sim_callsign_number()
        
        for line in sorted_lines:
            duration = line.duration or 1.0  # type: ignore
            is_sim = line.is_sim or False  # type: ignore
            
            # Find time slot based on crew member (instructor/pilot) availability
            if line.pilot2_crew_id:  # type: ignore
                start_time = self._find_available_slot(
                    line.pilot2_crew_id.id,  # type: ignore
                    instructor_busy,
                    base_start_time,
                    duration
                )
            else:
                start_time = base_start_time
            
            # Find available aircraft (filtered by simulator type)
            aircraft_id = False
            if is_sim:
                # For simulators, show all available simulator aircraft
                domain = [
                    ('is_airworthy', '=', True),
                    ('aircraft_type_id.is_simulator', '=', True),
                ]
            else:
                # For regular flights, filter by allowed aircraft types
                domain = [
                    ('is_airworthy', '=', True),
                    ('aircraft_type_id', 'in', line.aircraft_type_ids.ids if line.aircraft_type_ids else []),  # type: ignore
                    ('aircraft_type_id.is_simulator', '=', False),
                ]
            
            available_aircraft = self.env['fs.aircraft'].search(domain)  # type: ignore
            
            # Find a time slot where BOTH instructor AND aircraft are available
            # Keep incrementing time until we find a slot where both are free
            last_end = self.last_end_time or 15.75  # Default 15:45
            max_attempts = 100  # Prevent infinite loop
            attempt = 0
            while attempt < max_attempts:
                # Check if flight would end after the last allowed end time
                if start_time + duration > last_end:
                    break
                
                # Check if any aircraft is available at current start_time
                for aircraft in available_aircraft:
                    if self._is_slot_available(aircraft.id, aircraft_busy, start_time, duration):
                        # Check crew member (instructor/pilot) is also available at this time
                        if not line.pilot2_crew_id or self._is_slot_available(line.pilot2_crew_id.id, instructor_busy, start_time, duration):  # type: ignore
                            aircraft_id = aircraft.id
                            aircraft_busy.setdefault(aircraft.id, []).append(
                                (start_time, start_time + duration + buffer_hours)
                            )
                            break
                
                if aircraft_id:
                    break  # Found both aircraft and instructor slot
                
                # No aircraft available at this time, try next slot
                start_time += 0.25  # Try 15 minutes later
                attempt += 1
            
            # Mark crew member busy
            if line.pilot2_crew_id:  # type: ignore
                instructor_busy.setdefault(line.pilot2_crew_id.id, []).append(  # type: ignore
                    (start_time, start_time + duration + buffer_hours)
                )
            
            # Assign callsign number based on type
            callsign_number = 0
            if not line.is_added_mission:  # type: ignore
                if is_sim:
                    callsign_number = next_sim_callsign
                    next_sim_callsign += 1
                else:
                    callsign_number = next_aircraft_callsign
                    next_aircraft_callsign += 1
            
            # Update line with assigned values
            line.write({  # type: ignore
                'start_time': start_time,
                'aircraft_id': aircraft_id,
                'callsign_number': callsign_number,
            })

    def action_reschedule(self):
        """Reschedule unlocked lines while preserving locked line assignments.
        
        Locked lines keep their assigned time, aircraft, and callsign.
        Unlocked lines are rescheduled around the locked constraints.
        """
        # Sort lines: Normal Aircraft -> ADD Missions -> Simulators, order by instructor then sequence
        sorted_lines = self.line_ids.sorted(key=lambda l: (
            2 if l.is_sim else (1 if l.is_added_mission else 0), # type: ignore
            (l.pilot2_crew_id.name or '') if l.pilot2_crew_id else '', # type: ignore
            l.sequence # type: ignore
        ))  # type: ignore
        
        # Update sequence numbers to reflect the new order
        for i, line in enumerate(sorted_lines):
            line.sequence = i + 1  # type: ignore
        
        # Get existing flights for this date
        existing_flights = self.env['fs.scheduled.flight'].search([
            ('date', '=', self.date),
            ('status', '!=', 'cancelled'),
        ])
        
        # Get buffer time from config
        buffer_minutes = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.scheduling_buffer_minutes', '15'
        ))
        buffer_hours = buffer_minutes / 60.0
        
        # Build occupancy maps from existing flights
        instructor_busy = {}
        aircraft_busy = {}
        
        for flight in existing_flights:
            end_time = flight.start_time + flight.duration + buffer_hours  # type: ignore
            if flight.instructor_id:  # type: ignore
                instructor_busy.setdefault(flight.instructor_id.id, []).append(  # type: ignore
                    (flight.start_time, end_time)  # type: ignore
                )
            if flight.aircraft_id:  # type: ignore
                aircraft_busy.setdefault(flight.aircraft_id.id, []).append(  # type: ignore
                    (flight.start_time, end_time)  # type: ignore
                )
        
        # Add locked lines to occupancy maps first (as constraints)
        locked_lines = sorted_lines.filtered(lambda l: l.is_locked)  # type: ignore
        for line in locked_lines:
            duration = line.duration or 1.0  # type: ignore
            end_time = line.start_time + duration + buffer_hours  # type: ignore
            
            if line.pilot2_crew_id:  # type: ignore
                instructor_busy.setdefault(line.pilot2_crew_id.id, []).append(  # type: ignore
                    (line.start_time, end_time)  # type: ignore
                )
            if line.aircraft_id:  # type: ignore
                aircraft_busy.setdefault(line.aircraft_id.id, []).append(  # type: ignore
                    (line.start_time, end_time)  # type: ignore
                )
        
        # Get used callsign numbers from locked lines
        locked_aircraft_callsigns = set()
        locked_sim_callsigns = set()
        for line in locked_lines:
            if line.is_sim:  # type: ignore
                locked_sim_callsigns.add(line.callsign_number)  # type: ignore
            else:
                locked_aircraft_callsigns.add(line.callsign_number)  # type: ignore
        
        base_start_time = self.first_start_time or 8.0
        last_end = self.last_end_time or 15.75
        
        # Separate callsign sequences for aircraft and simulators
        next_aircraft_callsign = self.next_callsign_number
        next_sim_callsign = self._get_next_sim_callsign_number()
        
        # Reschedule only unlocked lines
        unlocked_lines = sorted_lines.filtered(lambda l: not l.is_locked)  # type: ignore
        
        for line in unlocked_lines:
            duration = line.duration or 1.0  # type: ignore
            is_sim = line.is_sim or False  # type: ignore
            
            # Find time slot based on crew member availability
            if line.pilot2_crew_id:  # type: ignore
                start_time = self._find_available_slot(
                    line.pilot2_crew_id.id,  # type: ignore
                    instructor_busy,
                    base_start_time,
                    duration
                )
            else:
                start_time = base_start_time
            
            # Find available aircraft
            aircraft_id = False
            if is_sim:
                domain = [
                    ('is_airworthy', '=', True),
                    ('aircraft_type_id.is_simulator', '=', True),
                ]
            else:
                domain = [
                    ('is_airworthy', '=', True),
                    ('aircraft_type_id', 'in', line.aircraft_type_ids.ids if line.aircraft_type_ids else []),  # type: ignore
                    ('aircraft_type_id.is_simulator', '=', False),
                ]
            
            available_aircraft = self.env['fs.aircraft'].search(domain)  # type: ignore
            
            # Find a time slot where BOTH instructor AND aircraft are available
            max_attempts = 100
            attempt = 0
            while attempt < max_attempts:
                if start_time + duration > last_end:
                    break
                
                for aircraft in available_aircraft:
                    if self._is_slot_available(aircraft.id, aircraft_busy, start_time, duration):
                        if not line.pilot2_crew_id or self._is_slot_available(line.pilot2_crew_id.id, instructor_busy, start_time, duration):  # type: ignore
                            aircraft_id = aircraft.id
                            aircraft_busy.setdefault(aircraft.id, []).append(
                                (start_time, start_time + duration + buffer_hours)
                            )
                            break
                
                if aircraft_id:
                    break
                
                start_time += 0.25
                attempt += 1
            
            # Mark crew member busy
            if line.pilot2_crew_id:  # type: ignore
                instructor_busy.setdefault(line.pilot2_crew_id.id, []).append(  # type: ignore
                    (start_time, start_time + duration + buffer_hours)
                )
            
            # Assign callsign number (skip numbers used by locked lines)
            callsign_number = 0
            if not line.is_added_mission:  # type: ignore
                if is_sim:
                    while next_sim_callsign in locked_sim_callsigns:
                        next_sim_callsign += 1
                    callsign_number = next_sim_callsign
                    next_sim_callsign += 1
                else:
                    while next_aircraft_callsign in locked_aircraft_callsigns:
                        next_aircraft_callsign += 1
                    callsign_number = next_aircraft_callsign
                    next_aircraft_callsign += 1
            
            # Update line with assigned values
            line.write({  # type: ignore
                'start_time': start_time,
                'aircraft_id': aircraft_id,
                'callsign_number': callsign_number,
            })
        
        return self._reopen_wizard()

    # === Step 3: Final Scheduling ===
    def action_schedule(self):
        """Create the scheduled flights."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No flights to schedule."))

        scheduled_flights = self.env['fs.scheduled.flight']
        aircraft_prefix = self.callsign_prefix or 'ABS'
        sim_prefix = 'SIM'

        # Sort lines by sequence for consistent ordering
        for line in self.line_ids.sorted(key=lambda l: l.sequence):  # type: ignore
            callsign = line.callsign_display  # type: ignore
            
            scheduled_flights.create({
                'callsign': callsign,
                'date': self.date,
                'start_time': line.start_time,  # type: ignore
                'duration': line.duration,  # type: ignore
                'flight_category': line.flight_category,  # type: ignore
                'pilot1_crew_id': line.pilot1_crew_id.id if line.pilot1_crew_id else False,  # type: ignore
                'pilot1_function': line.pilot1_function,  # type: ignore
                'pilot2_crew_id': line.pilot2_crew_id.id if line.pilot2_crew_id else False,  # type: ignore
                'pilot2_function': line.pilot2_function,  # type: ignore
                'flight_type_id': line.flight_type_id.id if line.flight_type_id else False,  # type: ignore
                'aircraft_id': line.aircraft_id.id if line.aircraft_id else False,  # type: ignore
                'mission_id': line.mission_id.id if line.mission_id else False,  # type: ignore
                'activity_id': line.activity_id.id if line.activity_id else False,  # type: ignore
                'custom_activity_id': line.custom_activity_id.id if line.custom_activity_id else False,  # type: ignore
                'route_id': line.route_id.id if line.route_id else False,  # type: ignore
            })

        return {
            'type': 'ir.actions.act_window',
            'name': _("Today's Schedule"),
            'res_model': 'fs.scheduled.flight',
            'view_mode': 'timeline,list,form',
            'target': 'current',
            'domain': [('date', '=', self.date)],
        }
