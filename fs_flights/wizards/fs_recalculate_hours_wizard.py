# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsRecalculateHoursWizard(models.TransientModel):
    """Wizard to recalculate flight hours from completed flights.
    
    This wizard compares stored totals with calculated values from flights
    and allows administrators to selectively apply corrections.
    """
    _name = 'fs.recalculate.hours.wizard'
    _description = 'Recalculate Hours Wizard'

    line_ids = fields.One2many(
        'fs.recalculate.hours.line',
        'wizard_id',
        string='Differences',
    )
    include_instructors = fields.Boolean(string='Instructors', default=True)
    include_pilots = fields.Boolean(string='Pilots', default=True)
    include_students = fields.Boolean(string='Students', default=True)
    include_aircraft = fields.Boolean(string='Aircraft', default=True)
    show_only_differences = fields.Boolean(
        string='Show Only Differences',
        default=True,
        help="If checked, only entities with discrepancies are shown.",
    )

    def action_calculate(self):
        """Calculate differences between stored and calculated values."""
        self.ensure_one()
        self.line_ids.unlink()
        
        lines = []
        Flight = self.env['fs.flight']
        
        # Helper to get hours from flights
        def get_flight_hours(domain):
            flights = Flight.search(domain + [('status', '=', 'done')])
            return sum(flights.mapped('distributed_hours'))
        
        # === Instructors ===
        if self.include_instructors:
            for instructor in self.env['fs.instructor'].search([]):
                calc_flight = self._calculate_person_hours(instructor, 'instructor', 'flight')
                calc_instruction = self._calculate_person_hours(instructor, 'instructor', 'instruction')
                calc_sim = self._calculate_person_hours(instructor, 'instructor', 'sim')
                
                if instructor.total_flight_hours != calc_flight or not self.show_only_differences:
                    lines.append({
                        'wizard_id': self.id,
                        'entity_type': 'instructor',
                        'entity_id': instructor.id,
                        'entity_name': instructor.name,
                        'field_name': 'total_flight_hours',
                        'current_value': instructor.total_flight_hours,
                        'calculated_value': calc_flight,
                    })
                if instructor.total_instruction_hours != calc_instruction or not self.show_only_differences:
                    lines.append({
                        'wizard_id': self.id,
                        'entity_type': 'instructor',
                        'entity_id': instructor.id,
                        'entity_name': instructor.name,
                        'field_name': 'total_instruction_hours',
                        'current_value': instructor.total_instruction_hours,
                        'calculated_value': calc_instruction,
                    })
                if instructor.total_sim_hours != calc_sim or not self.show_only_differences:
                    lines.append({
                        'wizard_id': self.id,
                        'entity_type': 'instructor',
                        'entity_id': instructor.id,
                        'entity_name': instructor.name,
                        'field_name': 'total_sim_hours',
                        'current_value': instructor.total_sim_hours,
                        'calculated_value': calc_sim,
                    })
        
        # === Pilots ===
        if self.include_pilots:
            for pilot in self.env['fs.pilot'].search([]):
                calc_flight = self._calculate_person_hours(pilot, 'pilot', 'flight')
                calc_sim = self._calculate_person_hours(pilot, 'pilot', 'sim')
                
                if pilot.total_flight_hours != calc_flight or not self.show_only_differences:
                    lines.append({
                        'wizard_id': self.id,
                        'entity_type': 'pilot',
                        'entity_id': pilot.id,
                        'entity_name': pilot.name,
                        'field_name': 'total_flight_hours',
                        'current_value': pilot.total_flight_hours,
                        'calculated_value': calc_flight,
                    })
                if pilot.total_sim_hours != calc_sim or not self.show_only_differences:
                    lines.append({
                        'wizard_id': self.id,
                        'entity_type': 'pilot',
                        'entity_id': pilot.id,
                        'entity_name': pilot.name,
                        'field_name': 'total_sim_hours',
                        'current_value': pilot.total_sim_hours,
                        'calculated_value': calc_sim,
                    })
        
        # === Students ===
        if self.include_students:
            for student in self.env['fs.student'].search([]):
                calc_flight = self._calculate_student_hours(student, 'flight')
                calc_sim = self._calculate_student_hours(student, 'sim')
                
                if student.total_flight_hours != calc_flight or not self.show_only_differences:
                    lines.append({
                        'wizard_id': self.id,
                        'entity_type': 'student',
                        'entity_id': student.id,
                        'entity_name': student.name,
                        'field_name': 'total_flight_hours',
                        'current_value': student.total_flight_hours,
                        'calculated_value': calc_flight,
                    })
                if student.total_sim_hours != calc_sim or not self.show_only_differences:
                    lines.append({
                        'wizard_id': self.id,
                        'entity_type': 'student',
                        'entity_id': student.id,
                        'entity_name': student.name,
                        'field_name': 'total_sim_hours',
                        'current_value': student.total_sim_hours,
                        'calculated_value': calc_sim,
                    })
        
        # === Aircraft ===
        if self.include_aircraft:
            for aircraft in self.env['fs.aircraft'].search([]):
                calc_hours = sum(Flight.search([
                    ('aircraft_id', '=', aircraft.id),
                    ('status', '=', 'done'),
                ]).mapped('distributed_hours'))
                
                if aircraft.total_hours != calc_hours or not self.show_only_differences:
                    lines.append({
                        'wizard_id': self.id,
                        'entity_type': 'aircraft',
                        'entity_id': aircraft.id,
                        'entity_name': aircraft.registration,
                        'field_name': 'total_hours',
                        'current_value': aircraft.total_hours,
                        'calculated_value': calc_hours,
                    })
        
        # Create all lines
        self.env['fs.recalculate.hours.line'].create(lines)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _calculate_person_hours(self, person, person_type, hour_type):
        """Calculate hours for a person from completed flights."""
        Flight = self.env['fs.flight']
        model_name = f'fs.{person_type}'
        
        # Build domain for flights where this person was crew
        domain = [
            ('status', '=', 'done'),
            '|',
            '&', ('pilot1_crew_id.source_model', '=', model_name),
                 ('pilot1_crew_id.source_id', '=', person.id),
            '&', ('pilot2_crew_id.source_model', '=', model_name),
                 ('pilot2_crew_id.source_id', '=', person.id),
        ]
        
        flights = Flight.search(domain)
        total = 0.0
        
        for flight in flights:
            # Determine if sim
            is_sim = self._is_flight_sim(flight)
            
            if hour_type == 'sim' and is_sim:
                total += flight.distributed_hours
            elif hour_type == 'flight' and not is_sim:
                total += flight.distributed_hours
            elif hour_type == 'instruction' and not is_sim:
                # Check if assigned with instructor function
                if self._is_instructor_on_flight(person, flight):
                    total += flight.distributed_hours
        
        # Add initial experience
        initial = self.env['fs.initial.experience'].search([
            ('person_type', '=', person_type),
            (f'{person_type}_id', '=', person.id),
            ('is_applied', '=', True),
        ])
        if hour_type == 'flight':
            total += sum(initial.mapped('initial_flight_hours'))
        elif hour_type == 'sim':
            total += sum(initial.mapped('initial_sim_hours'))
        elif hour_type == 'instruction':
            total += sum(initial.mapped('initial_instruction_hours'))
        
        return total

    def _calculate_student_hours(self, student, hour_type):
        """Calculate hours for a student from completed flights."""
        Flight = self.env['fs.flight']
        
        flights = Flight.search([
            ('student_id', '=', student.id),
            ('status', '=', 'done'),
        ])
        
        total = 0.0
        for flight in flights:
            is_sim = self._is_flight_sim(flight)
            if hour_type == 'sim' and is_sim:
                total += flight.distributed_hours
            elif hour_type == 'flight' and not is_sim:
                total += flight.distributed_hours
        
        # Add initial experience
        initial = self.env['fs.initial.experience'].search([
            ('person_type', '=', 'student'),
            ('student_id', '=', student.id),
            ('is_applied', '=', True),
        ])
        if hour_type == 'flight':
            total += sum(initial.mapped('initial_flight_hours'))
        elif hour_type == 'sim':
            total += sum(initial.mapped('initial_sim_hours'))
        
        return total

    def _is_flight_sim(self, flight):
        """Check if flight is a simulator session."""
        if flight.mission_id and hasattr(flight.mission_id, 'is_sim') and flight.mission_id.is_sim:
            return True
        if flight.activity_id and hasattr(flight.activity_id, 'is_sim') and flight.activity_id.is_sim:
            return True
        if flight.aircraft_id and flight.aircraft_id.category_id:
            return getattr(flight.aircraft_id.category_id, 'is_simulator', False)
        return False

    def _is_instructor_on_flight(self, instructor, flight):
        """Check if instructor was assigned with instructor function."""
        if (flight.pilot1_crew_id and 
            flight.pilot1_crew_id.source_model == 'fs.instructor' and
            flight.pilot1_crew_id.source_id == instructor.id and
            flight.pilot1_function == 'instructor'):
            return True
        if (flight.pilot2_crew_id and 
            flight.pilot2_crew_id.source_model == 'fs.instructor' and
            flight.pilot2_crew_id.source_id == instructor.id and
            flight.pilot2_function == 'instructor'):
            return True
        return False

    def action_apply_selected(self):
        """Apply selected corrections to entity totals."""
        for line in self.line_ids.filtered('apply'):
            line.action_apply()
        
        return {'type': 'ir.actions.act_window_close'}


class FsRecalculateHoursLine(models.TransientModel):
    """Individual difference line in the recalculate wizard."""
    _name = 'fs.recalculate.hours.line'
    _description = 'Recalculate Hours Line'

    wizard_id = fields.Many2one(
        'fs.recalculate.hours.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    entity_type = fields.Selection([
        ('instructor', 'Instructor'),
        ('pilot', 'Pilot'),
        ('student', 'Student'),
        ('aircraft', 'Aircraft'),
    ], string='Type', required=True)
    entity_id = fields.Integer(string='Entity ID')
    entity_name = fields.Char(string='Name')
    field_name = fields.Char(string='Field')
    current_value = fields.Float(string='Current', digits=(16, 2))
    calculated_value = fields.Float(string='Calculated', digits=(16, 2))
    difference = fields.Float(
        string='Difference',
        compute='_compute_difference',
        digits=(16, 2),
    )
    apply = fields.Boolean(string='Apply', default=True)

    @api.depends('current_value', 'calculated_value')
    def _compute_difference(self):
        for line in self:
            line.difference = line.calculated_value - line.current_value

    def action_apply(self):
        """Apply the correction to this entity."""
        self.ensure_one()
        
        model_map = {
            'instructor': 'fs.instructor',
            'pilot': 'fs.pilot',
            'student': 'fs.student',
            'aircraft': 'fs.aircraft',
        }
        
        model = model_map.get(self.entity_type)
        if not model:
            return
        
        entity = self.env[model].browse(self.entity_id)
        if entity.exists() and self.field_name:
            entity.sudo().write({str(self.field_name): self.calculated_value})
