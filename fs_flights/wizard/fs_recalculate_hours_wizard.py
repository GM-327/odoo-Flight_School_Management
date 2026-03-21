# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsRecalculateHoursWizard(models.TransientModel):
    """Wizard to recalculate flight hours from completed flights.
    
    Shows a preview of calculated values vs current values,
    highlighting differences. Administrators can select which
    values to apply.
    """
    _name = 'fs.recalculate.hours.wizard'
    _description = 'Recalculate Hours Wizard'

    state = fields.Selection([
        ('select', 'Select Scope'),
        ('preview', 'Preview Changes'),
        ('done', 'Done'),
    ], default='select')

    entity_type = fields.Selection([
        ('all', 'All Entities'),
        ('instructors', 'Instructors Only'),
        ('pilots', 'Pilots Only'),
        ('students', 'Students Only'),
        ('aircraft', 'Aircraft Only'),
    ], string='Recalculate For', default='all', required=True)

    line_ids = fields.One2many(
        'fs.recalculate.hours.line',
        'wizard_id',
        string='Changes',
    )

    changes_count = fields.Integer(
        compute='_compute_changes_count',
    )
    
    @api.depends('line_ids.difference')
    def _compute_changes_count(self):
        for record in self:
            record.changes_count = len(record.line_ids.filtered(lambda x: x.difference != 0))

    def action_calculate(self):
        """Calculate differences and show preview."""
        self.ensure_one()
        self.line_ids.unlink()
        
        lines = []
        Flight = self.env['fs.flight']
        
        # Get all completed flights
        completed_flights = Flight.search([('status', '=', 'done')])
        
        if self.entity_type in ('all', 'aircraft'):
            lines.extend(self._calculate_aircraft_hours(completed_flights))
        
        if self.entity_type in ('all', 'instructors'):
            lines.extend(self._calculate_person_hours('fs.instructor', completed_flights))
        
        if self.entity_type in ('all', 'pilots'):
            lines.extend(self._calculate_person_hours('fs.pilot', completed_flights))
        
        if self.entity_type in ('all', 'students'):
            lines.extend(self._calculate_person_hours('fs.student', completed_flights))
        
        if lines:
            self.env['fs.recalculate.hours.line'].create(lines)
        
        self.state = 'preview'
        return self._reopen_wizard()

    def _calculate_aircraft_hours(self, flights):
        """Calculate aircraft hours from flights."""
        lines = []
        Aircraft = self.env['fs.aircraft']
        
        # Group flights by aircraft
        aircraft_hours = {}
        for flight in flights:
            if flight.aircraft_id:
                key = flight.aircraft_id.id
                aircraft_hours.setdefault(key, 0.0)
                aircraft_hours[key] += flight.distributed_hours or 0.0
        
        # Compare with current values
        for aircraft_id, calc_hours in aircraft_hours.items():
            aircraft = Aircraft.browse(aircraft_id)
            if aircraft.exists():
                current = aircraft.total_hours or 0.0
                if abs(calc_hours - current) > 0.01:  # Tolerance for float comparison
                    lines.append({
                        'wizard_id': self.id,
                        'entity_model': 'fs.aircraft',
                        'entity_id': aircraft_id,
                        'entity_name': aircraft.registration,
                        'field_name': 'total_hours',
                        'current_value': current,
                        'calculated_value': calc_hours,
                        'apply': True,
                    })
        return lines

    def _calculate_person_hours(self, model_name, flights):
        """Calculate person hours from flights."""
        lines = []
        Model = self.env[model_name]
        
        # Determine member type for crew matching
        member_type_map = {
            'fs.instructor': 'instructor',
            'fs.pilot': 'pilot',
            'fs.student': 'student',
        }
        member_type = member_type_map.get(model_name, '')
        
        # Collect hours per person per field
        person_hours = {}  # {person_id: {'total_flight_hours': x, 'total_sim_hours': y, ...}}
        
        for flight in flights:
            hours = flight.distributed_hours or 0.0
            if hours <= 0:
                continue
            
            is_sim = flight._is_simulator_session() if hasattr(flight, '_is_simulator_session') else False
            
            # Check P1 and P2 crew members
            for crew, func_field in [(flight.pilot1_crew_id, flight.pilot1_function),
                                      (flight.pilot2_crew_id, flight.pilot2_function)]:
                if not crew or crew.member_type != member_type:
                    continue
                
                person_id = crew.source_id
                if not person_id:
                    continue
                
                person_hours.setdefault(person_id, {
                    'total_flight_hours': 0.0,
                    'total_sim_hours': 0.0,
                    'solo_hours': 0.0,
                    'total_instruction_hours': 0.0,
                })
                
                func_config = flight._get_pilot_function_config(func_field) if hasattr(flight, '_get_pilot_function_config') else {}
                
                if is_sim:
                    person_hours[person_id]['total_sim_hours'] += hours
                else:
                    if func_config.get('is_counted_flight', True):
                        person_hours[person_id]['total_flight_hours'] += hours
                    if func_config.get('is_counted_instructor', False):
                        person_hours[person_id]['total_instruction_hours'] += hours
                    if func_config.get('is_counted_solo', False):
                        person_hours[person_id]['solo_hours'] += hours
            
            # For students, also check direct student assignment
            if model_name == 'fs.student' and flight.flight_category == 'student_training' and flight.student_id:
                person_id = flight.student_id.id
                person_hours.setdefault(person_id, {
                    'total_flight_hours': 0.0,
                    'total_sim_hours': 0.0,
                    'solo_hours': 0.0,
                })
                if is_sim:
                    person_hours[person_id]['total_sim_hours'] += hours
                else:
                    person_hours[person_id]['total_flight_hours'] += hours
        
        # Compare with current values
        for person_id, calc_data in person_hours.items():
            person = Model.browse(person_id)
            if not person.exists():
                continue
            
            for field_name, calc_value in calc_data.items():
                if not hasattr(person, field_name):
                    continue
                current = getattr(person, field_name) or 0.0
                if abs(calc_value - current) > 0.01:
                    lines.append({
                        'wizard_id': self.id,
                        'entity_model': model_name,
                        'entity_id': person_id,
                        'entity_name': person.name,
                        'field_name': field_name,
                        'current_value': current,
                        'calculated_value': calc_value,
                        'apply': True,
                    })
        
        return lines

    def action_apply(self):
        """Apply selected changes."""
        self.ensure_one()
        
        lines_to_apply = self.line_ids.filtered(lambda x: x.apply and x.difference != 0)
        
        for line in lines_to_apply:
            Model = self.env[line.entity_model]
            record = Model.browse(line.entity_id)
            if record.exists():
                record.sudo().write({line.field_name: line.calculated_value})
        
        self.state = 'done'
        return self._reopen_wizard()

    def action_back(self):
        """Go back to selection."""
        self.state = 'select'
        self.line_ids.unlink()
        return self._reopen_wizard()

    def _reopen_wizard(self):
        """Reopen the wizard form."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class FsRecalculateHoursLine(models.TransientModel):
    """Line item for recalculate hours wizard."""
    _name = 'fs.recalculate.hours.line'
    _description = 'Recalculate Hours Line'

    wizard_id = fields.Many2one(
        'fs.recalculate.hours.wizard',
        required=True,
        ondelete='cascade',
    )
    entity_model = fields.Char(
        string='Model',
        required=True,
    )
    entity_id = fields.Integer(
        string='Record ID',
        required=True,
    )
    entity_name = fields.Char(
        string='Entity',
    )
    field_name = fields.Char(
        string='Field',
    )
    current_value = fields.Float(
        string='Current Value',
    )
    calculated_value = fields.Float(
        string='Calculated Value',
    )
    difference = fields.Float(
        string='Difference',
        compute='_compute_difference',
        store=True,
    )
    apply = fields.Boolean(
        string='Apply',
        default=True,
    )

    @api.depends('current_value', 'calculated_value')
    def _compute_difference(self):
        for record in self:
            record.difference = record.calculated_value - record.current_value
