"""
Spare Part Mapping Engine.

This module maps equipment failures and root causes to required spare parts.
"""
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PartMapping:
    """Mapping between equipment/root cause and spare part."""
    mapping_id: str
    equipment_type: str
    root_cause: str
    part_id: str
    part_name: str
    part_number: str
    quantity_required: int
    urgency: str  # critical, high, medium, low
    description: str
    created_at: datetime = field(default_factory=datetime.now)


class SparePartMappingEngine:
    """
    Map equipment failures to required spare parts.
    
    Features:
    - Root cause to spare part mapping
    - Equipment type to spare part mapping
    - Multi-part recommendations
    - Quantity estimation
    """
    
    # Default mappings for steel plant equipment
    DEFAULT_MAPPINGS = [
        # Bearing failures
        {
            'equipment_type': 'motor',
            'root_cause': 'bearing wear',
            'part_id': 'SP001',
            'part_name': 'Deep Groove Ball Bearing',
            'part_number': 'B6205',
            'quantity_required': 1,
            'urgency': 'high',
            'description': 'Primary bearing replacement for motor'
        },
        {
            'equipment_type': 'motor',
            'root_cause': 'bearing failure',
            'part_id': 'SP001',
            'part_name': 'Deep Groove Ball Bearing',
            'part_number': 'B6205',
            'quantity_required': 2,
            'urgency': 'critical',
            'description': 'Replace both bearings - drive and non-drive end'
        },
        {
            'equipment_type': 'motor',
            'root_cause': 'bearing failure',
            'part_id': 'SP003',
            'part_name': 'Bearing Lubricant',
            'part_number': 'BL-001',
            'quantity_required': 1,
            'urgency': 'medium',
            'description': 'Lubricant for new bearing installation'
        },
        # Pump failures
        {
            'equipment_type': 'pump',
            'root_cause': 'pump blockage',
            'part_id': 'SP002',
            'part_name': 'Mechanical Seal',
            'part_number': 'MS-100',
            'quantity_required': 1,
            'urgency': 'high',
            'description': 'Replace worn mechanical seal'
        },
        {
            'equipment_type': 'pump',
            'root_cause': 'seal failure',
            'part_id': 'SP002',
            'part_name': 'Mechanical Seal',
            'part_number': 'MS-100',
            'quantity_required': 1,
            'urgency': 'critical',
            'description': 'Mechanical seal replacement due to leakage'
        },
        {
            'equipment_type': 'pump',
            'root_cause': 'pump blockage',
            'part_id': 'SP008',
            'part_name': 'Gasket Sheet',
            'part_number': 'GS-500',
            'quantity_required': 2,
            'urgency': 'medium',
            'description': 'Gaskets for pump housing'
        },
        # Motor overheating
        {
            'equipment_type': 'motor',
            'root_cause': 'motor overheating',
            'part_id': 'SP009',
            'part_name': 'Thermal Protector',
            'part_number': 'TP-25',
            'quantity_required': 1,
            'urgency': 'high',
            'description': 'Thermal overload protector'
        },
        {
            'equipment_type': 'motor',
            'root_cause': 'cooling system failure',
            'part_id': 'SP010',
            'part_name': 'Cooling Fan Blade',
            'part_number': 'CFB-150',
            'quantity_required': 1,
            'urgency': 'high',
            'description': 'Cooling fan for motor temperature control'
        },
        # Electrical faults
        {
            'equipment_type': 'motor',
            'root_cause': 'electrical fault',
            'part_id': 'SP006',
            'part_name': 'Electrical Contactor',
            'part_number': 'CT-25A',
            'quantity_required': 1,
            'urgency': 'high',
            'description': 'Main power contactor replacement'
        },
        # Compressor
        {
            'equipment_type': 'compressor',
            'root_cause': 'air filter blockage',
            'part_id': 'SP005',
            'part_name': 'Air Filter Element',
            'part_number': 'AF-STD',
            'quantity_required': 2,
            'urgency': 'high',
            'description': 'Replace clogged air filters'
        },
        {
            'equipment_type': 'compressor',
            'root_cause': 'oil degradation',
            'part_id': 'SP007',
            'part_name': 'Oil Filter',
            'part_number': 'OF-STD',
            'quantity_required': 1,
            'urgency': 'medium',
            'description': 'Replace oil filter during service'
        },
        {
            'equipment_type': 'compressor',
            'root_cause': 'lubrication failure',
            'part_id': 'SP003',
            'part_name': 'Bearing Lubricant',
            'part_number': 'BL-001',
            'quantity_required': 2,
            'urgency': 'high',
            'description': 'Compressor oil replacement'
        },
        # Shaft misalignment
        {
            'equipment_type': 'motor',
            'root_cause': 'shaft misalignment',
            'part_id': 'SP004',
            'part_name': 'Coupling Spider',
            'part_number': 'CS-150',
            'quantity_required': 1,
            'urgency': 'medium',
            'description': 'Replace worn coupling element'
        },
        # General consumables
        {
            'equipment_type': 'general',
            'root_cause': 'gasket failure',
            'part_id': 'SP008',
            'part_name': 'Gasket Sheet',
            'part_number': 'GS-500',
            'quantity_required': 3,
            'urgency': 'medium',
            'description': 'Various gasket replacements'
        }
    ]
    
    def __init__(self):
        self.mappings: Dict[str, PartMapping] = {}
        self._load_default_mappings()
    
    def _load_default_mappings(self):
        """Load default mappings."""
        for mapping_data in self.DEFAULT_MAPPINGS:
            mapping = PartMapping(
                mapping_id=str(uuid.uuid4()),
                equipment_type=mapping_data['equipment_type'],
                root_cause=mapping_data['root_cause'],
                part_id=mapping_data['part_id'],
                part_name=mapping_data['part_name'],
                part_number=mapping_data['part_number'],
                quantity_required=mapping_data['quantity_required'],
                urgency=mapping_data['urgency'],
                description=mapping_data['description']
            )
            self.mappings[mapping.mapping_id] = mapping
    
    def get_spare_parts(
        self,
        equipment_type: str,
        root_cause: str,
        failure_probability: Optional[float] = None,
        multiple: bool = True
    ) -> List[PartMapping]:
        """
        Get required spare parts for equipment and root cause.
        
        Args:
            equipment_type: Type of equipment
            root_cause: Identified root cause
            failure_probability: Failure probability (for urgency adjustment)
            multiple: Whether to return all matches or just best match
            
        Returns:
            List of PartMapping objects
        """
        matches = []
        root_cause_lower = root_cause.lower()
        
        for mapping in self.mappings.values():
            # Check equipment type match
            if mapping.equipment_type.lower() != equipment_type.lower():
                continue
            
            # Check root cause match (partial match allowed)
            if (mapping.root_cause.lower() in root_cause_lower or 
                root_cause_lower in mapping.root_cause.lower()):
                # Adjust urgency based on failure probability
                if failure_probability and failure_probability > 0.8:
                    adjusted_urgency = 'critical'
                elif failure_probability and failure_probability > 0.6:
                    adjusted_urgency = 'high'
                else:
                    adjusted_urgency = mapping.urgency
                
                mapping.urgency = adjusted_urgency
                matches.append(mapping)
        
        if multiple:
            return matches
        else:
            # Return most urgent match
            if not matches:
                return []
            
            urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            matches.sort(key=lambda m: urgency_order.get(m.urgency, 4))
            return [matches[0]]
    
    def get_parts_for_multiple_root_causes(
        self,
        equipment_type: str,
        root_causes: List[str]
    ) -> List[PartMapping]:
        """Get spare parts for multiple root causes."""
        all_parts = []
        seen_part_ids = set()
        
        for root_cause in root_causes:
            parts = self.get_spare_parts(equipment_type, root_cause, multiple=True)
            for part in parts:
                if part.part_id not in seen_part_ids:
                    all_parts.append(part)
                    seen_part_ids.add(part.part_id)
        
        return all_parts
    
    def add_mapping(self, mapping: PartMapping) -> bool:
        """Add a new mapping."""
        if mapping.mapping_id in self.mappings:
            return False
        self.mappings[mapping.mapping_id] = mapping
        return True
    
    def remove_mapping(self, mapping_id: str) -> bool:
        """Remove a mapping."""
        if mapping_id in self.mappings:
            del self.mappings[mapping_id]
            return True
        return False
    
    def get_all_mappings(self) -> List[PartMapping]:
        """Get all mappings."""
        return list(self.mappings.values())
    
    def get_mappings_by_part(self, part_id: str) -> List[PartMapping]:
        """Get all mappings for a specific part."""
        return [m for m in self.mappings.values() if m.part_id == part_id]
    
    def get_mappings_by_equipment(self, equipment_type: str) -> List[PartMapping]:
        """Get all mappings for a specific equipment type."""
        return [m for m in self.mappings.values() 
                if m.equipment_type.lower() == equipment_type.lower()]


# Singleton instance
_mapping_engine: Optional[SparePartMappingEngine] = None


def get_mapping_engine() -> SparePartMappingEngine:
    """Get global mapping engine instance."""
    global _mapping_engine
    if _mapping_engine is None:
        _mapping_engine = SparePartMappingEngine()
    return _mapping_engine