"""
Maintenance Planner.

This module generates preventive maintenance schedules
based on equipment condition and historical data.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class MaintenanceTask:
    """Single maintenance task."""
    task_id: str
    task_name: str
    description: str
    frequency: str  # daily, weekly, monthly, quarterly, yearly
    estimated_duration_hours: float
    priority: str  # P1, P2, P3, P4
    skills_required: List[str]
    parts_needed: List[str]
    estimated_cost: float


@dataclass
class MaintenanceSchedule:
    """Maintenance schedule for equipment."""
    schedule_id: str
    equipment_name: str
    created_at: datetime
    tasks: List[MaintenanceTask]
    total_weekly_hours: float
    total_monthly_hours: float
    estimated_annual_cost: float


class MaintenancePlanner:
    """
    Generate preventive maintenance schedules.
    
    Creates optimized maintenance schedules based on:
    - Equipment type and criticality
    - Historical maintenance data
    - Manufacturer recommendations
    - Current equipment condition
    """
    
    # Default maintenance tasks by equipment type
    DEFAULT_TASKS = {
        'motor': [
            {'name': 'Check bearing temperature', 'freq': 'daily', 'duration': 0.5, 'priority': 'P2', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Listen for unusual sounds', 'freq': 'daily', 'duration': 0.25, 'priority': 'P3', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Check vibration levels', 'freq': 'weekly', 'duration': 1.0, 'priority': 'P2', 'skills': ['vibration_analysis'], 'parts': [], 'cost': 0},
            {'name': 'Inspect electrical connections', 'freq': 'weekly', 'duration': 0.5, 'priority': 'P3', 'skills': ['electrical'], 'parts': [], 'cost': 0},
            {'name': 'Lubricate bearings', 'freq': 'monthly', 'duration': 2.0, 'priority': 'P2', 'skills': ['mechanical'], 'parts': ['lubricant'], 'cost': 50},
            {'name': 'Check insulation resistance', 'freq': 'quarterly', 'duration': 1.5, 'priority': 'P3', 'skills': ['electrical'], 'parts': [], 'cost': 0},
            {'name': 'Alignment check', 'freq': 'quarterly', 'duration': 2.0, 'priority': 'P2', 'skills': ['alignment'], 'parts': [], 'cost': 0},
            {'name': 'Complete motor inspection', 'freq': 'yearly', 'duration': 8.0, 'priority': 'P2', 'skills': ['mechanical', 'electrical'], 'parts': ['bearings', 'seals'], 'cost': 500}
        ],
        'pump': [
            {'name': 'Check flow rate', 'freq': 'daily', 'duration': 0.5, 'priority': 'P2', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Check pressure', 'freq': 'daily', 'duration': 0.25, 'priority': 'P2', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Inspect seals for leaks', 'freq': 'weekly', 'duration': 0.5, 'priority': 'P3', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Check strainer', 'freq': 'weekly', 'duration': 1.0, 'priority': 'P2', 'skills': ['mechanical'], 'parts': [], 'cost': 0},
            {'name': 'Lubricate bearings', 'freq': 'monthly', 'duration': 1.5, 'priority': 'P2', 'skills': ['mechanical'], 'parts': ['lubricant'], 'cost': 30},
            {'name': 'Clean impeller', 'freq': 'quarterly', 'duration': 4.0, 'priority': 'P3', 'skills': ['mechanical'], 'parts': [], 'cost': 0},
            {'name': 'Replace seals', 'freq': 'yearly', 'duration': 6.0, 'priority': 'P2', 'skills': ['mechanical'], 'parts': ['seals', 'gaskets'], 'cost': 200}
        ],
        'compressor': [
            {'name': 'Check oil level', 'freq': 'daily', 'duration': 0.5, 'priority': 'P1', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Check temperature', 'freq': 'daily', 'duration': 0.25, 'priority': 'P2', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Drain condensate', 'freq': 'daily', 'duration': 0.25, 'priority': 'P3', 'skills': ['operation'], 'parts': [], 'cost': 0},
            {'name': 'Check filters', 'freq': 'weekly', 'duration': 1.0, 'priority': 'P2', 'skills': ['mechanical'], 'parts': [], 'cost': 0},
            {'name': 'Change oil', 'freq': 'monthly', 'duration': 2.0, 'priority': 'P2', 'skills': ['mechanical'], 'parts': ['oil', 'filter'], 'cost': 150},
            {'name': 'Replace air filter', 'freq': 'quarterly', 'duration': 1.5, 'priority': 'P3', 'skills': ['mechanical'], 'parts': ['air_filter'], 'cost': 100},
            {'name': 'Full service', 'freq': 'yearly', 'duration': 12.0, 'priority': 'P1', 'skills': ['mechanical', 'electrical'], 'parts': ['oil', 'filters', 'belts'], 'cost': 800}
        ],
        'conveyor': [
            {'name': 'Check belt tension', 'freq': 'daily', 'duration': 0.5, 'priority': 'P2', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Listen for belt noise', 'freq': 'daily', 'duration': 0.25, 'priority': 'P3', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Check rollers', 'freq': 'weekly', 'duration': 1.0, 'priority': 'P3', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Lubricate bearings', 'freq': 'weekly', 'duration': 1.5, 'priority': 'P2', 'skills': ['mechanical'], 'parts': ['lubricant'], 'cost': 20},
            {'name': 'Inspect belt wear', 'freq': 'monthly', 'duration': 2.0, 'priority': 'P2', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Replace rollers', 'freq': 'yearly', 'duration': 8.0, 'priority': 'P3', 'skills': ['mechanical'], 'parts': ['rollers'], 'cost': 600}
        ],
        'default': [
            {'name': 'Visual inspection', 'freq': 'daily', 'duration': 0.5, 'priority': 'P3', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Check operating parameters', 'freq': 'weekly', 'duration': 1.0, 'priority': 'P3', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Lubrication', 'freq': 'monthly', 'duration': 1.5, 'priority': 'P2', 'skills': ['mechanical'], 'parts': ['lubricant'], 'cost': 30},
            {'name': 'Clean components', 'freq': 'quarterly', 'duration': 2.0, 'priority': 'P3', 'skills': ['mechanical'], 'parts': [], 'cost': 0},
            {'name': 'Full inspection', 'freq': 'yearly', 'duration': 6.0, 'priority': 'P2', 'skills': ['mechanical', 'electrical'], 'parts': ['filters'], 'cost': 200}
        ]
    }
    
    def generate_schedule(
        self,
        equipment_name: str,
        equipment_type: str,
        criticality: str = 'medium',
        condition: str = 'good'
    ) -> MaintenanceSchedule:
        """
        Generate maintenance schedule for equipment.
        
        Args:
            equipment_name: Name of equipment
            equipment_type: Type of equipment (motor, pump, etc.)
            criticality: Equipment criticality (low, medium, high, critical)
            condition: Current condition (good, fair, poor)
            
        Returns:
            MaintenanceSchedule with all tasks
        """
        schedule_id = str(uuid.uuid4())
        
        # Get tasks for equipment type
        tasks_data = self.DEFAULT_TASKS.get(
            equipment_type.lower(),
            self.DEFAULT_TASKS['default']
        )
        
        # Adjust based on criticality
        if criticality == 'critical':
            # More frequent tasks
            tasks_data = self._increase_frequency(tasks_data)
        elif criticality == 'low':
            # Less frequent tasks
            tasks_data = self._decrease_frequency(tasks_data)
        
        # Adjust based on condition
        if condition == 'poor':
            # Add more repair-oriented tasks
            tasks_data = self._add_repair_tasks(tasks_data)
        
        tasks = []
        weekly_hours = 0
        monthly_hours = 0
        annual_cost = 0
        
        for task_data in tasks_data:
            task = MaintenanceTask(
                task_id=str(uuid.uuid4()),
                task_name=task_data['name'],
                description=f"Regular {task_data['freq']} maintenance: {task_data['name']}",
                frequency=task_data['freq'],
                estimated_duration_hours=task_data['duration'],
                priority=task_data['priority'],
                skills_required=task_data['skills'],
                parts_needed=task_data['parts'],
                estimated_cost=task_data['cost']
            )
            tasks.append(task)
            
            # Calculate time based on frequency
            if task_data['freq'] == 'daily':
                weekly_hours += task_data['duration'] * 7
                monthly_hours += task_data['duration'] * 30
                annual_cost += task_data['cost'] * 365
            elif task_data['freq'] == 'weekly':
                weekly_hours += task_data['duration']
                monthly_hours += task_data['duration'] * 4
                annual_cost += task_data['cost'] * 52
            elif task_data['freq'] == 'monthly':
                monthly_hours += task_data['duration']
                annual_cost += task_data['cost'] * 12
            elif task_data['freq'] == 'quarterly':
                monthly_hours += task_data['duration'] / 3
                annual_cost += task_data['cost'] * 4
            elif task_data['freq'] == 'yearly':
                monthly_hours += task_data['duration'] / 12
                annual_cost += task_data['cost']
        
        return MaintenanceSchedule(
            schedule_id=schedule_id,
            equipment_name=equipment_name,
            created_at=datetime.now(),
            tasks=tasks,
            total_weekly_hours=round(weekly_hours, 1),
            total_monthly_hours=round(monthly_hours, 1),
            estimated_annual_cost=round(annual_cost, 2)
        )
    
    def _increase_frequency(self, tasks_data: List[Dict]) -> List[Dict]:
        """Increase task frequency for critical equipment."""
        frequency_map = {
            'daily': 'daily',  # Keep daily
            'weekly': 'daily',  # Upgrade weekly to daily
            'monthly': 'weekly',  # Upgrade monthly to weekly
            'quarterly': 'monthly',  # Upgrade quarterly to monthly
            'yearly': 'quarterly'  # Upgrade yearly to quarterly
        }
        
        return [{**t, 'freq': frequency_map.get(t['freq'], t['freq'])} for t in tasks_data]
    
    def _decrease_frequency(self, tasks_data: List[Dict]) -> List[Dict]:
        """Decrease task frequency for low criticality equipment."""
        frequency_map = {
            'daily': 'weekly',  # Downgrade daily to weekly
            'weekly': 'monthly',  # Downgrade weekly to monthly
            'monthly': 'quarterly',  # Downgrade monthly to quarterly
            'quarterly': 'yearly',  # Downgrade quarterly to yearly
            'yearly': 'yearly'  # Keep yearly
        }
        
        return [{**t, 'freq': frequency_map.get(t['freq'], t['freq'])} for t in tasks_data]
    
    def _add_repair_tasks(self, tasks_data: List[Dict]) -> List[Dict]:
        """Add repair tasks for poor condition equipment."""
        repair_tasks = [
            {'name': 'Additional inspection for wear', 'freq': 'weekly', 'duration': 1.0, 'priority': 'P2', 'skills': ['inspection'], 'parts': [], 'cost': 0},
            {'name': 'Replace worn components', 'freq': 'monthly', 'duration': 4.0, 'priority': 'P1', 'skills': ['mechanical'], 'parts': ['various'], 'cost': 300}
        ]
        return tasks_data + repair_tasks
    
    def get_next_tasks(
        self,
        schedule: MaintenanceSchedule,
        days_ahead: int = 7
    ) -> List[MaintenanceTask]:
        """Get upcoming maintenance tasks."""
        # For simplicity, return tasks by frequency
        upcoming = []
        
        for task in schedule.tasks:
            if task.frequency == 'daily':
                upcoming.append(task)
            elif task.frequency == 'weekly' and schedule.total_weekly_hours > 0:
                upcoming.append(task)
            elif task.frequency == 'monthly':
                upcoming.append(task)
        
        return upcoming[:10]  # Limit to 10 tasks


# Singleton instance
_maintenance_planner: Optional[MaintenancePlanner] = None


def get_maintenance_planner() -> MaintenancePlanner:
    """Get global maintenance planner instance."""
    global _maintenance_planner
    if _maintenance_planner is None:
        _maintenance_planner = MaintenancePlanner()
    return _maintenance_planner