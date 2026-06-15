"""
Repair Guide Generator.

This module generates step-by-step repair guidance
based on SOPs, manuals, and historical maintenance records.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RepairStep:
    """Single repair step."""
    step_number: int
    action: str
    description: str
    estimated_time_minutes: int
    safety_requirements: List[str]
    tools_required: List[str]
    source: str


@dataclass
class RepairGuide:
    """Complete repair guide."""
    guide_id: str
    equipment_name: str
    repair_type: str  # bearing_replacement, cleaning, alignment, etc.
    estimated_total_time_minutes: int
    steps: List[RepairStep]
    required_parts: List[str]
    required_tools: List[str]
    safety_warnings: List[str]
    post_repair_checks: List[str]


class RepairGuideGenerator:
    """
    Generate step-by-step repair guides.
    
    Uses templates and historical data to create
    detailed repair procedures.
    """
    
    # Repair guide templates
    REPAIR_GUIDES = {
        'bearing replacement': {
            'steps': [
                {
                    'action': 'Prepare work area',
                    'description': 'Clear work area and gather tools',
                    'time': 15,
                    'safety': ['Wear PPE', 'Clear floor'],
                    'tools': ['Tool kit', 'Cleaning supplies']
                },
                {
                    'action': 'Shut down equipment',
                    'description': 'Turn off equipment and allow to cool',
                    'time': 10,
                    'safety': ['Lockout-tagout', 'Allow cooling'],
                    'tools': ['Lockout devices']
                },
                {
                    'action': 'Remove components',
                    'description': 'Remove coupling, guards, and access panels',
                    'time': 30,
                    'safety': ['Use lifting equipment', 'Support heavy parts'],
                    'tools': ['Wrench set', 'Socket set', 'Lifting equipment']
                },
                {
                    'action': 'Remove old bearing',
                    'description': 'Use bearing puller to remove damaged bearing',
                    'time': 45,
                    'safety': ['Wear gloves', 'Support shaft'],
                    'tools': ['Bearing puller', 'Heat gun', 'Bearing splitter']
                },
                {
                    'action': 'Clean components',
                    'description': 'Clean shaft, housing, and surrounding area',
                    'time': 20,
                    'safety': ['Wear gloves', 'Use cleaning solvent'],
                    'tools': ['Cleaning solvent', 'Brushes', 'Rags']
                },
                {
                    'action': 'Inspect components',
                    'description': 'Check shaft, housing, and seals for wear',
                    'time': 15,
                    'safety': ['Use flashlight'],
                    'tools': ['Flashlight', 'Measuring tools']
                },
                {
                    'action': 'Install new bearing',
                    'description': 'Heat bearing and press onto shaft',
                    'time': 30,
                    'safety': ['Use heat-resistant gloves', 'Press evenly'],
                    'tools': ['Bearing heater', 'Press tool', 'Torque wrench']
                },
                {
                    'action': 'Reassemble equipment',
                    'description': 'Reinstall coupling, guards, and panels',
                    'time': 30,
                    'safety': ['Check alignment', 'Tighten bolts'],
                    'tools': ['Torque wrench', 'Alignment tools']
                },
                {
                    'action': 'Test equipment',
                    'description': 'Run equipment and check for proper operation',
                    'time': 30,
                    'safety': ['Monitor for异常', 'Check temperature'],
                    'tools': ['Vibration analyzer', 'Thermal camera']
                }
            ],
            'parts': ['Bearing', 'Seals', 'Lubricant', 'Gaskets'],
            'tools': ['Bearing puller', 'Bearing heater', 'Torque wrench', 'Alignment tools'],
            'safety': [
                'Follow lockout-tagout procedures',
                'Use proper lifting techniques',
                'Allow equipment to cool before work',
                'Wear appropriate PPE'
            ],
            'post_checks': [
                'Check bearing temperature',
                'Verify vibration levels',
                'Check lubrication',
                'Test operation at various speeds'
            ]
        },
        'pump cleaning': {
            'steps': [
                {
                    'action': 'Isolate pump',
                    'description': 'Close valves and isolate pump from system',
                    'time': 10,
                    'safety': ['Wear gloves'],
                    'tools': ['Wrench']
                },
                {
                    'action': 'Drain pump',
                    'description': 'Remove drain plug and drain fluid',
                    'time': 15,
                    'safety': ['Collect fluid', 'Wear gloves'],
                    'tools': ['Drain pan', 'Wrench']
                },
                {
                    'action': 'Remove cover',
                    'description': 'Remove pump cover and impeller',
                    'time': 20,
                    'safety': ['Support cover'],
                    'tools': ['Wrench set', 'Socket set']
                },
                {
                    'action': 'Clean components',
                    'description': 'Clean impeller, volute, and seals',
                    'time': 30,
                    'safety': ['Use solvent in ventilated area'],
                    'tools': ['Brushes', 'Cleaning solvent', 'Rags']
                },
                {
                    'action': 'Inspect wear',
                    'description': 'Check impeller and volute for wear',
                    'time': 15,
                    'safety': [],
                    'tools': ['Flashlight', 'Measuring tools']
                },
                {
                    'action': 'Replace seals',
                    'description': 'Replace mechanical seals if worn',
                    'time': 25,
                    'safety': ['Handle seals carefully'],
                    'tools': ['Seal installer', 'Lubricant']
                },
                {
                    'action': 'Reassemble',
                    'description': 'Reassemble pump with new gaskets',
                    'time': 20,
                    'safety': ['Check gasket alignment'],
                    'tools': ['Torque wrench', 'Gasket sealant']
                },
                {
                    'action': 'Test pump',
                    'description': 'Reconnect and test pump operation',
                    'time': 20,
                    'safety': ['Check for leaks', 'Monitor pressure'],
                    'tools': ['Pressure gauge', 'Stethoscope']
                }
            ],
            'parts': ['Gaskets', 'Seals', 'O-rings'],
            'tools': ['Wrench set', 'Gasket scraper', 'Torque wrench'],
            'safety': ['Allow pump to cool', 'Collect fluids properly'],
            'post_checks': ['Check for leaks', 'Verify flow rate', 'Check pressure']
        },
        'motor alignment': {
            'steps': [
                {
                    'action': 'Prepare equipment',
                    'description': 'Clean alignment surfaces and gather tools',
                    'time': 15,
                    'safety': ['Clear work area'],
                    'tools': ['Cleaning supplies', 'Alignment kit']
                },
                {
                    'action': 'Measure alignment',
                    'description': 'Use laser alignment tool to measure offset and angle',
                    'time': 20,
                    'safety': [],
                    'tools': ['Laser alignment tool', 'Feeler gauges']
                },
                {
                    'action': 'Loosen bolts',
                    'description': 'Loosen motor mounting bolts',
                    'time': 10,
                    'safety': ['Support motor'],
                    'tools': ['Wrench set']
                },
                {
                    'action': 'Adjust motor',
                    'description': 'Use shims and bolts to align motor',
                    'time': 30,
                    'safety': ['Work in pairs'],
                    'tools': ['Shim set', 'Torque wrench', 'Spirit level']
                },
                {
                    'action': 'Tighten bolts',
                    'description': 'Tighten mounting bolts to specification',
                    'time': 15,
                    'safety': ['Torque to spec'],
                    'tools': ['Torque wrench']
                },
                {
                    'action': 'Verify alignment',
                    'description': 'Re-check alignment after tightening',
                    'time': 15,
                    'safety': [],
                    'tools': ['Laser alignment tool']
                },
                {
                    'action': 'Test run',
                    'description': 'Run equipment and check vibration',
                    'time': 30,
                    'safety': ['Monitor vibration', 'Check temperature'],
                    'tools': ['Vibration analyzer']
                }
            ],
            'parts': ['Shims', 'Bolts'],
            'tools': ['Laser alignment tool', 'Torque wrench', 'Feeler gauges'],
            'safety': ['Support heavy equipment', 'Use proper lifting'],
            'post_checks': ['Check vibration', 'Verify temperature', 'Listen for unusual sounds']
        },
        'lubrication': {
            'steps': [
                {
                    'action': 'Prepare',
                    'description': 'Gather correct lubricant and tools',
                    'time': 10,
                    'safety': ['Use correct lubricant grade'],
                    'tools': ['Lubricant', 'Grease gun', 'Oil can']
                },
                {
                    'action': 'Clean fittings',
                    'description': 'Clean grease fittings and surrounding area',
                    'time': 5,
                    'safety': [],
                    'tools': ['Clean rag', 'Solvent']
                },
                {
                    'action': 'Apply lubricant',
                    'description': 'Apply correct amount of lubricant',
                    'time': 10,
                    'safety': ['Do not over-grease'],
                    'tools': ['Grease gun', 'Oil applicator']
                },
                {
                    'action': 'Clean excess',
                    'description': 'Remove excess lubricant',
                    'time': 5,
                    'safety': ['Dispose properly'],
                    'tools': ['Clean rag']
                },
                {
                    'action': 'Record',
                    'description': 'Record lubrication in maintenance log',
                    'time': 5,
                    'safety': [],
                    'tools': ['Maintenance log']
                }
            ],
            'parts': ['Lubricant'],
            'tools': ['Grease gun', 'Oil can', 'Clean rags'],
            'safety': ['Use correct lubricant', 'Avoid over-lubrication'],
            'post_checks': ['Check for leaks', 'Verify operation']
        }
    }
    
    def generate_repair_guide(
        self,
        equipment_name: str,
        repair_type: str,
        root_cause: Optional[str] = None
    ) -> RepairGuide:
        """
        Generate repair guide for equipment.
        
        Args:
            equipment_name: Name of equipment
            repair_type: Type of repair (bearing_replacement, cleaning, etc.)
            root_cause: Optional root cause for context
            
        Returns:
            RepairGuide with step-by-step instructions
        """
        guide_id = str(uuid.uuid4())
        
        # Get template or create generic
        template = self._get_template(repair_type, root_cause)
        
        steps = []
        total_time = 0
        
        for i, step_data in enumerate(template['steps'], 1):
            step = RepairStep(
                step_number=i,
                action=step_data['action'],
                description=step_data['description'],
                estimated_time_minutes=step_data['time'],
                safety_requirements=step_data.get('safety', []),
                tools_required=step_data.get('tools', []),
                source=f"SOP - {repair_type}"
            )
            steps.append(step)
            total_time += step_data['time']
        
        return RepairGuide(
            guide_id=guide_id,
            equipment_name=equipment_name,
            repair_type=repair_type,
            estimated_total_time_minutes=total_time,
            steps=steps,
            required_parts=template['parts'],
            required_tools=template['tools'],
            safety_warnings=template['safety'],
            post_repair_checks=template['post_checks']
        )
    
    def _get_template(
        self,
        repair_type: str,
        root_cause: Optional[str]
    ) -> Dict[str, Any]:
        """Get template based on repair type and root cause."""
        # Map repair types
        type_map = {
            'bearing': 'bearing replacement',
            'bearing_replacement': 'bearing replacement',
            'cleaning': 'pump cleaning',
            'pump_cleaning': 'pump cleaning',
            'alignment': 'motor alignment',
            'motor_alignment': 'motor alignment',
            'lubrication': 'lubrication',
            'general': 'bearing replacement'  # Default
        }
        
        template_key = type_map.get(repair_type.lower(), 'bearing replacement')
        
        if template_key in self.REPAIR_GUIDES:
            return self.REPAIR_GUIDES[template_key]
        
        return self.REPAIR_GUIDES['bearing replacement']
    
    def get_available_repair_types(self) -> List[str]:
        """Get list of available repair types."""
        return list(self.REPAIR_GUIDES.keys())


# Singleton instance
_repair_guide_generator: Optional[RepairGuideGenerator] = None


def get_repair_guide_generator() -> RepairGuideGenerator:
    """Get global repair guide generator instance."""
    global _repair_guide_generator
    if _repair_guide_generator is None:
        _repair_guide_generator = RepairGuideGenerator()
    return _repair_guide_generator