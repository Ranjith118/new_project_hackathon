"""
Maintenance Scheduling Engine.

This module generates optimized maintenance schedules based on
priorities, available resources, and production constraints.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.decision_support.prioritization_engine import get_prioritization_engine, MaintenancePriority


@dataclass
class ScheduledMaintenance:
    """Scheduled maintenance task."""
    schedule_id: str
    equipment_id: str
    equipment_name: str
    maintenance_type: str
    scheduled_date: datetime
    priority: str
    estimated_duration_hours: float
    estimated_downtime: float
    technicians_required: int
    parts_needed: List[str]
    prerequisites: List[str]
    status: str  # scheduled, in_progress, completed, cancelled
    notes: str = ""


@dataclass
class MaintenanceSchedule:
    """Complete maintenance schedule."""
    schedule_id: str
    week_start: datetime
    created_at: datetime
    tasks: List[ScheduledMaintenance]
    total_tasks: int
    total_downtime_hours: float
    production_impact: str
    summary: Dict[str, Any]


class SchedulingEngine:
    """
    Generate optimized maintenance schedules.
    
    Objectives:
    - Minimize total downtime
    - Reduce production impact
    - Utilize available resources efficiently
    - Respect maintenance priorities
    """
    
    # Days of the week
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    def __init__(self):
        self.prioritization = get_prioritization_engine()
        self.schedules: List[MaintenanceSchedule] = []
    
    def generate_schedule(
        self,
        priorities: List[MaintenancePriority],
        start_date: Optional[datetime] = None,
        max_daily_downtime: float = 8.0,
        available_technicians: int = 5
    ) -> MaintenanceSchedule:
        """
        Generate maintenance schedule.
        
        Args:
            priorities: List of maintenance priorities
            start_date: Schedule start date
            max_daily_downtime: Maximum allowed downtime per day (hours)
            available_technicians: Number of available technicians
            
        Returns:
            MaintenanceSchedule with optimized schedule
        """
        if start_date is None:
            start_date = datetime.now()
        
        # Start from Monday
        while start_date.weekday() != 0:
            start_date += timedelta(days=1)
        
        tasks = []
        daily_downtime = {day: 0.0 for day in self.DAYS}
        
        # Sort priorities
        sorted_priorities = sorted(priorities, key=lambda p: p.priority_score, reverse=True)
        
        # Schedule high priority first
        for priority in sorted_priorities:
            if priority.priority_level in ['P1', 'P2']:
                # Find best day for this maintenance
                day = self._find_best_day(
                    priority, 
                    start_date, 
                    daily_downtime, 
                    max_daily_downtime
                )
                
                if day:
                    task = self._create_scheduled_task(priority, day)
                    tasks.append(task)
                    
                    # Update daily downtime
                    day_name = self.DAYS[day.weekday()]
                    daily_downtime[day_name] += task.estimated_downtime
        
        # Add lower priority if time permits
        for priority in sorted_priorities:
            if priority.priority_level not in ['P1', 'P2']:
                # Schedule in second week if time permits
                day = self._find_best_day(
                    priority,
                    start_date + timedelta(days=7),
                    daily_downtime,
                    max_daily_downtime
                )
                
                if day:
                    task = self._create_scheduled_task(priority, day)
                    tasks.append(task)
                    
                    day_name = self.DAYS[day.weekday()]
                    daily_downtime[day_name] += task.estimated_downtime
        
        # Create schedule
        schedule = MaintenanceSchedule(
            schedule_id=str(uuid.uuid4()),
            week_start=start_date,
            created_at=datetime.now(),
            tasks=tasks,
            total_tasks=len(tasks),
            total_downtime_hours=sum(t.estimated_downtime for t in tasks),
            production_impact=self._assess_production_impact(tasks),
            summary=self._generate_schedule_summary(tasks, daily_downtime)
        )
        
        self.schedules.append(schedule)
        return schedule
    
    def _find_best_day(
        self,
        priority: MaintenancePriority,
        start_date: datetime,
        daily_downtime: Dict[str, float],
        max_daily_downtime: float
    ) -> Optional[datetime]:
        """Find the best day to schedule maintenance."""
        # For P1, schedule immediately
        if priority.priority_level == 'P1':
            for i in range(7):
                day = start_date + timedelta(days=i)
                day_name = self.DAYS[day.weekday()]
                if daily_downtime[day_name] + priority.estimated_downtime <= max_daily_downtime:
                    return day
            # If no room, schedule on first day anyway
            return start_date
        
        # For P2, schedule within first week if possible
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_name = self.DAYS[day.weekday()]
            if daily_downtime[day_name] + priority.estimated_downtime <= max_daily_downtime:
                return day
        
        # Schedule in second week
        for i in range(7, 14):
            day = start_date + timedelta(days=i)
            day_name = self.DAYS[day.weekday()]
            if daily_downtime[day_name] + priority.estimated_downtime <= max_daily_downtime:
                return day
        
        return None
    
    def _create_scheduled_task(
        self,
        priority: MaintenancePriority,
        day: datetime
    ) -> ScheduledMaintenance:
        """Create scheduled maintenance task."""
        maintenance_type = self._get_maintenance_type(priority)
        
        return ScheduledMaintenance(
            schedule_id=str(uuid.uuid4()),
            equipment_id=priority.equipment_id,
            equipment_name=priority.equipment_name,
            maintenance_type=maintenance_type,
            scheduled_date=day,
            priority=priority.priority_level,
            estimated_duration_hours=priority.estimated_downtime * 1.5,
            estimated_downtime=priority.estimated_downtime,
            technicians_required=self._get_technicians_needed(priority),
            parts_needed=self._get_parts_needed(priority),
            prerequisites=self._get_prerequisites(priority),
            status='scheduled',
            notes=f"Priority {priority.priority_level} maintenance"
        )
    
    def _get_maintenance_type(self, priority: MaintenancePriority) -> str:
        """Determine maintenance type."""
        if priority.priority_level == 'P1':
            return 'Emergency Repair'
        elif priority.priority_level == 'P2':
            return 'Urgent Maintenance'
        elif priority.rul_days <= 30:
            return 'Scheduled Repair'
        else:
            return 'Preventive Maintenance'
    
    def _get_technicians_needed(self, priority: MaintenancePriority) -> int:
        """Determine number of technicians needed."""
        if priority.priority_level == 'P1':
            return 3
        elif priority.priority_level == 'P2':
            return 2
        else:
            return 1
    
    def _get_parts_needed(self, priority: MaintenancePriority) -> List[str]:
        """Get required parts for maintenance."""
        # Simplified - would integrate with procurement
        if 'bearing' in priority.equipment_name.lower():
            return ['Bearing B6205', 'Lubricant', 'Seals']
        elif 'motor' in priority.equipment_name.lower():
            return ['Bearing Kit', 'Thermal Protector', 'Gaskets']
        elif 'pump' in priority.equipment_name.lower():
            return ['Mechanical Seal', 'Gaskets', 'O-Rings']
        else:
            return ['General Maintenance Supplies']
    
    def _get_prerequisites(self, priority: MaintenancePriority) -> List[str]:
        """Get prerequisite tasks."""
        prereqs = []
        if priority.priority_level in ['P1', 'P2']:
            prereqs.append('Work permit approval')
            prereqs.append('Lockout-tagout')
        return prereqs
    
    def _assess_production_impact(self, tasks: List[ScheduledMaintenance]) -> str:
        """Assess overall production impact."""
        total_downtime = sum(t.estimated_downtime for t in tasks)
        
        if total_downtime > 40:
            return 'Critical'
        elif total_downtime > 25:
            return 'High'
        elif total_downtime > 15:
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_schedule_summary(
        self,
        tasks: List[ScheduledMaintenance],
        daily_downtime: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate schedule summary."""
        by_priority = {'P1': 0, 'P2': 0, 'P3': 0, 'P4': 0}
        by_type = {}
        
        for task in tasks:
            by_priority[task.priority] = by_priority.get(task.priority, 0) + 1
            by_type[task.maintenance_type] = by_type.get(task.maintenance_type, 0) + 1
        
        return {
            'by_priority': by_priority,
            'by_type': by_type,
            'daily_downtime': daily_downtime,
            'p1_tasks': by_priority['P1'],
            'p2_tasks': by_priority['P2']
        }
    
    def get_latest_schedule(self) -> Optional[MaintenanceSchedule]:
        """Get most recent schedule."""
        return self.schedules[-1] if self.schedules else None
    
    def get_schedule_by_id(self, schedule_id: str) -> Optional[MaintenanceSchedule]:
        """Get schedule by ID."""
        for schedule in self.schedules:
            if schedule.schedule_id == schedule_id:
                return schedule
        return None


# Singleton instance
_scheduling_engine: Optional[SchedulingEngine] = None


def get_scheduling_engine() -> SchedulingEngine:
    """Get global scheduling engine instance."""
    global _scheduling_engine
    if _scheduling_engine is None:
        _scheduling_engine = SchedulingEngine()
    return _scheduling_engine