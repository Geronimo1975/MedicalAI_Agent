from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from db import db
from db.schema import appointments, doctorSchedule, users
from drizzle_orm import eq, and_, or_, desc, asc

@dataclass
class TimeSlot:
    start_time: datetime
    end_time: datetime
    doctor_id: int
    score: float = 0.0

class AppointmentOptimizer:
    def __init__(self):
        self.min_appointment_duration = 15  # minutes
        self.max_appointment_duration = 120  # minutes
        self.scheduling_weights = {
            'priority': {
                'urgent': 1.0,
                'high': 0.8,
                'medium': 0.6,
                'low': 0.4
            },
            'preferred_time_match': 0.3,
            'equipment_availability': 0.2,
            'doctor_specialty_match': 0.2,
            'patient_history': 0.1,
            'wait_time': 0.1,
            'rescheduling_impact': -0.2
        }

    async def find_optimal_slots(
        self,
        patient_id: int,
        doctor_id: int,
        appointment_type: str,
        duration: int,
        preferred_times: List[Dict[str, datetime]],
        required_equipment: List[str] = None,
        priority: str = "medium"
    ) -> List[TimeSlot]:
        """Find optimal appointment slots based on various constraints."""
        
        # Get doctor's schedule
        schedule = await self._get_doctor_schedule(doctor_id)
        if not schedule:
            return []

        # Get existing appointments
        existing_appointments = await self._get_doctor_appointments(doctor_id)
        
        # Generate possible time slots
        available_slots = self._generate_available_slots(
            schedule,
            existing_appointments,
            duration,
            preferred_times
        )

        # Score and rank slots
        scored_slots = self._score_slots(
            available_slots,
            priority,
            preferred_times,
            required_equipment,
            existing_appointments
        )

        # Sort by score and return top slots
        scored_slots.sort(key=lambda x: x.score, reverse=True)
        return scored_slots[:5]  # Return top 5 slots

    def _score_slots(
        self,
        slots: List[TimeSlot],
        priority: str,
        preferred_times: List[Dict[str, datetime]],
        required_equipment: List[str],
        existing_appointments: List[Dict]
    ) -> List[TimeSlot]:
        """Score time slots based on various factors."""
        for slot in slots:
            score = 0.0
            
            # Base priority score
            score += self.scheduling_weights['priority'][priority]
            
            # Preferred time match
            if self._is_preferred_time(slot, preferred_times):
                score += self.scheduling_weights['preferred_time_match']
            
            # Equipment availability
            if required_equipment:
                equipment_score = self._check_equipment_availability(
                    slot,
                    required_equipment
                )
                score += equipment_score * self.scheduling_weights['equipment_availability']
            
            # Impact on existing appointments
            rescheduling_impact = self._calculate_rescheduling_impact(
                slot,
                existing_appointments
            )
            score += rescheduling_impact * self.scheduling_weights['rescheduling_impact']
            
            slot.score = max(0, min(1, score))  # Normalize score between 0 and 1
            
        return slots

    async def _get_doctor_schedule(self, doctor_id: int) -> List[Dict]:
        """Retrieve doctor's schedule from database."""
        schedule = await db.select().from_(doctorSchedule).where(
            eq(doctorSchedule.doctorId, doctor_id)
        )
        return schedule

    async def _get_doctor_appointments(self, doctor_id: int) -> List[Dict]:
        """Retrieve doctor's existing appointments."""
        existing = await db.select().from_(appointments).where(
            and_(
                eq(appointments.doctorId, doctor_id),
                eq(appointments.status, "scheduled")
            )
        )
        return existing

    def _generate_available_slots(
        self,
        schedule: List[Dict],
        existing_appointments: List[Dict],
        duration: int,
        preferred_times: List[Dict[str, datetime]]
    ) -> List[TimeSlot]:
        """Generate possible time slots based on schedule and existing appointments."""
        available_slots = []
        
        for day in schedule:
            # Convert schedule times to datetime
            day_start = self._parse_time(day['startTime'])
            day_end = self._parse_time(day['endTime'])
            
            current_time = day_start
            while current_time + timedelta(minutes=duration) <= day_end:
                # Check if slot conflicts with existing appointments
                if not self._has_conflict(
                    current_time,
                    current_time + timedelta(minutes=duration),
                    existing_appointments
                ):
                    available_slots.append(
                        TimeSlot(
                            start_time=current_time,
                            end_time=current_time + timedelta(minutes=duration),
                            doctor_id=day['doctorId']
                        )
                    )
                
                current_time += timedelta(minutes=self.min_appointment_duration)
        
        return available_slots

    def _has_conflict(
        self,
        start: datetime,
        end: datetime,
        existing_appointments: List[Dict]
    ) -> bool:
        """Check if a time slot conflicts with existing appointments."""
        for appt in existing_appointments:
            if (start < appt['endTime'] and end > appt['dateTime']):
                return True
        return False

    def _is_preferred_time(
        self,
        slot: TimeSlot,
        preferred_times: List[Dict[str, datetime]]
    ) -> bool:
        """Check if a slot falls within preferred times."""
        for pref in preferred_times:
            if (slot.start_time >= pref['start'] and
                slot.end_time <= pref['end']):
                return True
        return False

    def _check_equipment_availability(
        self,
        slot: TimeSlot,
        required_equipment: List[str]
    ) -> float:
        """Check equipment availability for a time slot."""
        # This is a placeholder - in a real system, you would check equipment
        # scheduling and availability in a separate table
        return 1.0

    def _calculate_rescheduling_impact(
        self,
        slot: TimeSlot,
        existing_appointments: List[Dict]
    ) -> float:
        """Calculate the impact of scheduling on existing appointments."""
        impact = 0.0
        for appt in existing_appointments:
            # Check proximity to other appointments
            time_diff = abs((slot.start_time - appt['dateTime']).total_seconds() / 3600)
            if time_diff < 1:  # If less than 1 hour apart
                impact -= 0.1
        return impact

    def _parse_time(self, time_str: str) -> datetime:
        """Convert time string to datetime object."""
        current_date = datetime.now().date()
        return datetime.combine(
            current_date,
            datetime.strptime(time_str, "%H:%M").time()
        )

    async def optimize_schedule(self, doctor_id: int) -> Dict:
        """Optimize a doctor's entire schedule by potentially rescheduling appointments."""
        scheduled_appointments = await self._get_doctor_appointments(doctor_id)
        schedule = await self._get_doctor_schedule(doctor_id)
        
        appointments_to_reschedule = []
        optimization_stats = {
            'total_appointments': len(scheduled_appointments),
            'rescheduled': 0,
            'optimization_score': 0.0,
            'recommended_changes': []
        }

        # Sort appointments by priority and scheduling score
        scheduled_appointments.sort(
            key=lambda x: (
                self.scheduling_weights['priority'][x['priority']],
                x['schedulingScore'] or 0
            ),
            reverse=True
        )

        for appt in scheduled_appointments:
            # Calculate current slot score
            current_slot = TimeSlot(
                start_time=appt['dateTime'],
                end_time=appt['endTime'],
                doctor_id=doctor_id
            )
            current_score = self._score_slots(
                [current_slot],
                appt['priority'],
                json.loads(appt['preferredTimeSlots'] or '[]'),
                appt['requiredEquipment'],
                [a for a in scheduled_appointments if a['id'] != appt['id']]
            )[0].score

            # Find potentially better slots
            better_slots = await self.find_optimal_slots(
                appt['patientId'],
                doctor_id,
                appt['type'],
                appt['duration'],
                json.loads(appt['preferredTimeSlots'] or '[]'),
                appt['requiredEquipment'],
                appt['priority']
            )

            # If we found a significantly better slot (>20% improvement)
            if better_slots and better_slots[0].score > current_score * 1.2:
                appointments_to_reschedule.append({
                    'appointment': appt,
                    'new_slot': better_slots[0],
                    'score_improvement': better_slots[0].score - current_score
                })
                optimization_stats['recommended_changes'].append({
                    'appointment_id': appt['id'],
                    'current_time': appt['dateTime'].isoformat(),
                    'suggested_time': better_slots[0].start_time.isoformat(),
                    'score_improvement': f"{((better_slots[0].score - current_score) * 100):.1f}%"
                })

        optimization_stats['rescheduled'] = len(appointments_to_reschedule)
        optimization_stats['optimization_score'] = sum(
            r['score_improvement'] for r in appointments_to_reschedule
        ) / len(scheduled_appointments) if scheduled_appointments else 0.0

        return optimization_stats
