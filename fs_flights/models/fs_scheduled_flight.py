# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
from datetime import datetime, timedelta

class FsScheduledFlight(models.Model):
    _name = 'fs.scheduled.flight'
    _inherit = ['fs.scheduled.flight']

    # === Push Architecture Actions ===

    @api.model
    def action_publish_day(self, date=None):
        """Publish scheduled flights for the date to fs.flight (Batch)."""
        if not date:
            date = fields.Date.context_today(self)
        
        flights = self.search([
            ('date', '=', date),
        ])
        
        created_count = 0
        Flight = self.env['fs.flight']
        
        for schedule in flights:
            # Check if already published
            existing = Flight.search([('scheduled_flight_id', '=', schedule.id)], limit=1)
            if existing:
                continue
            
            # Create Flight Record
            vals = {
                'scheduled_flight_id': schedule.id,
                'date': schedule.date, # type: ignore
                'callsign': schedule.callsign, # type: ignore
                'aircraft_id': schedule.aircraft_id.id, # type: ignore
                'pilot1_crew_id': schedule.pilot1_crew_id.id, # type: ignore
                'pilot1_function': schedule.pilot1_function, # type: ignore
                'pilot2_crew_id': schedule.pilot2_crew_id.id if schedule.pilot2_crew_id else False, # type: ignore
                'pilot2_function': schedule.pilot2_function, # type: ignore
                'flight_category': schedule.flight_category, # type: ignore
                'mission_id': schedule.mission_id.id if schedule.mission_id else False, # type: ignore
                'activity_id': schedule.activity_id.id if schedule.activity_id else False, # type: ignore
                'flight_type_id': schedule.flight_type_id.id if schedule.flight_type_id else False, # type: ignore
                'route_id': schedule.route_id.id if schedule.route_id else False, # type: ignore
                'scheduled_start': schedule.start_time, # type: ignore
                'scheduled_duration': schedule.duration, # type: ignore
                'status': 'scheduled',
            }
            Flight.create(vals)
            created_count += 1
            
        return created_count

    @api.model
    def cron_publish_today(self):
        """Daily cron job to publish today's flights."""
        self.action_publish_day()

    linked_flight_id = fields.Many2one(
        comodel_name='fs.flight',
        string='Execution Record',
        readonly=True,
        help="The actual flight record execution for this scheduled item."
    )

    # === Conflict Warning Overrides ===

    def _get_active_flight_buffer(self):
        """Helper to get buffer."""
        buffer_min = int(self.env['ir.config_parameter'].sudo().get_str( # type: ignore
            'flight_school.scheduling_buffer_minutes', '15'
        ))
        return timedelta(minutes=buffer_min)

    @api.depends('pilot2_crew_id', 'start_datetime', 'end_datetime')
    def _compute_instructor_conflict(self):
        """Extend to check Active Flight Conflicts."""
        # 1. Run super to check Schedule vs Schedule conflicts
        super()._compute_instructor_conflict() # type: ignore

        # 2. Check Active Flight Conflicts
        buffer = self._get_active_flight_buffer()
        Flight = self.env['fs.flight']
        
        for record in self:
            # If super already found a conflict, skip (or we could show both)
            if record.has_instructor_conflict: # type: ignore
                continue

            if not record.pilot2_crew_id: # type: ignore
                continue
            if record.pilot2_crew_id.member_type != 'instructor': # type: ignore
                continue
            if not record.start_datetime or not record.end_datetime: # type: ignore
                continue
            
            # Active Active Flights Search
            relevant_flights = Flight.search([
                ('date', '=', record.date), # type: ignore
                ('pilot2_crew_id', '=', record.pilot2_crew_id.id), # type: ignore
                ('status', '!=', 'cancelled'),
                ('scheduled_flight_id', '!=', record.id) # type: ignore
            ])
            
            for f in relevant_flights:
                # Convert float to datetime for comparison
                f_start = datetime.combine(f.date, datetime.min.time()) + timedelta(hours=f.scheduled_start) # type: ignore
                f_end = f_start + timedelta(hours=f.scheduled_duration or 0.0) # type: ignore
                
                if (f_start < record.end_datetime + buffer) and (f_end > record.start_datetime - buffer): # type: ignore
                    record.has_instructor_conflict = True # type: ignore
                    record.instructor_conflict_details = _( # type: ignore
                        "%(instructor)s: conflict with ACTIVE FLIGHT '%(callsign)s'",
                        instructor=record.pilot2_crew_id.name, # type: ignore
                        callsign=f.callsign, # type: ignore
                    )
                    break

    @api.depends('aircraft_id', 'start_datetime', 'end_datetime')
    def _compute_aircraft_conflict(self):
        """Extend to check Active Flight Conflicts."""
        # 1. Run super
        super()._compute_aircraft_conflict() # type: ignore

        # 2. Check Active Flights
        buffer = self._get_active_flight_buffer()
        Flight = self.env['fs.flight']
        
        for record in self:
            if record.has_aircraft_conflict: # type: ignore
                continue
                
            if not record.aircraft_id: # type: ignore
                continue
            if not record.start_datetime or not record.end_datetime: # type: ignore
                continue
            
            relevant_flights = Flight.search([
                ('date', '=', record.date), # type: ignore
                ('aircraft_id', '=', record.aircraft_id.id), # type: ignore
                ('status', '!=', 'cancelled'),
                ('scheduled_flight_id', '!=', record.id) # type: ignore
            ])
            
            for f in relevant_flights:
                f_start = datetime.combine(f.date, datetime.min.time()) + timedelta(hours=f.scheduled_start) # type: ignore
                f_end = f_start + timedelta(hours=f.scheduled_duration or 0.0) # type: ignore
                
                if (f_start < record.end_datetime + buffer) and (f_end > record.start_datetime - buffer): # type: ignore
                    record.has_aircraft_conflict = True # type: ignore
                    record.aircraft_conflict_details = _( # type: ignore
                        "%(aircraft)s: conflict with ACTIVE FLIGHT '%(callsign)s'",
                        aircraft=record.aircraft_id.registration, # type: ignore
                        callsign=f.callsign, # type: ignore
                    )
                    break
