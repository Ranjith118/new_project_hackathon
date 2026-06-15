"""
Spare Part Recommender.

This module recommends spare parts based on:
- Root cause analysis
- Equipment type
- Historical consumption
- Lead time requirements
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SpareRecommendation:
    """Single spare part recommendation."""
    part_id: str
    part_name: str
    part_number: str
    quantity: int
    urgency: str  # critical, high, medium, low
    lead_time_days: int
    estimated_cost: float
    supplier: Optional[str] = None
    reason: str = ""
    source: str = ""


@dataclass
class SparePartSet:
    """Complete set of spare part recommendations."""
    recommendation_id: str
    equipment_name: str
    root_cause: str
    timestamp: datetime
    parts: List[SpareRecommendation]
    total_estimated_cost: float
    critical_parts: List[str]


class SparePartRecommender:
    """
    Recommend spare parts based on root cause and equipment.
    """
    
    # Spare parts database by root cause and equipment type
    SPARE_PARTS_DB = {
        'bearing wear': {
            'motor': [
                {'name': 'Deep Groove Ball Bearing', 'part_no': 'B6205', 'cost': 45, 'lead_time': 5, 'supplier': 'Bearing Co.'},
                {'name': 'Sealing Ring', 'part_no': 'SR-6205', 'cost': 8, 'lead_time': 3, 'supplier': 'Seal Pro'},
                {'name': 'Bearing Lubricant', 'part_no': 'BL-001', 'cost': 25, 'lead_time': 2, 'supplier': 'Lubricant Inc'}
            ],
            'pump': [
                {'name': 'Bearing Assembly', 'part_no': 'BA-6205', 'cost': 65, 'lead_time': 7, 'supplier': 'Bearing Co.'},
                {'name': 'Mechanical Seal', 'part_no': 'MS-25', 'cost': 120, 'lead_time': 10, 'supplier': 'Seal Pro'}
            ],
            'default': [
                {'name': 'Ball Bearing 6205', 'part_no': 'BB-6205', 'cost': 50, 'lead_time': 5, 'supplier': 'Bearing Co.'},
                {'name': ' Bearing Locknut', 'part_no': 'BLN-M12', 'cost': 12, 'lead_time': 3, 'supplier': 'Hardware Inc'}
            ]
        },
        'bearing failure': {
            'motor': [
                {'name': 'Bearing Kit Complete', 'part_no': 'BK-6205', 'cost': 150, 'lead_time': 5, 'supplier': 'Bearing Co.'},
                {'name': 'Shaft Sleeve', 'part_no': 'SS-25', 'cost': 35, 'lead_time': 7, 'supplier': 'Metal Works'},
                {'name': 'End Cover Gasket', 'part_no': 'ECG-001', 'cost': 5, 'lead_time': 2, 'supplier': 'Seal Pro'}
            ],
            'pump': [
                {'name': 'Imeller Bearing Assembly', 'part_no': 'IBA-6305', 'cost': 200, 'lead_time': 10, 'supplier': 'Bearing Co.'},
                {'name': 'Lip Seal', 'part_no': 'LS-30', 'cost': 15, 'lead_time': 3, 'supplier': 'Seal Pro'}
            ],
            'default': [
                {'name': 'Replacement Bearing', 'part_no': 'RB-6205', 'cost': 75, 'lead_time': 7, 'supplier': 'Bearing Co.'}
            ]
        },
        'pump blockage': {
            'pump': [
                {'name': 'Strainer Basket', 'part_no': 'SB-100', 'cost': 85, 'lead_time': 5, 'supplier': 'Pump Parts'},
                {'name': 'O-Ring Set', 'part_no': 'ORS-100', 'cost': 20, 'lead_time': 2, 'supplier': 'Seal Pro'},
                {'name': 'Gasket Sheet', 'part_no': 'GS-500', 'cost': 30, 'lead_time': 3, 'supplier': 'Industrial Supply'}
            ],
            'default': [
                {'name': 'Filter Element', 'part_no': 'FE-100', 'cost': 45, 'lead_time': 3, 'supplier': 'Filter Co.'}
            ]
        },
        'motor overheating': {
            'motor': [
                {'name': 'Cooling Fan', 'part_no': 'CF-200', 'cost': 95, 'lead_time': 7, 'supplier': 'Fan Pro'},
                {'name': 'Thermal Protector', 'part_no': 'TP-25', 'cost': 40, 'lead_time': 5, 'supplier': 'Electrical Co.'},
                {'name': 'Terminal Box Gasket', 'part_no': 'TBG-001', 'cost': 8, 'lead_time': 2, 'supplier': 'Seal Pro'}
            ],
            'default': [
                {'name': 'Cooling Fan Blade', 'part_no': 'CFB-150', 'cost': 60, 'lead_time': 5, 'supplier': 'Fan Pro'}
            ]
        },
        'electrical fault': {
            'motor': [
                {'name': 'Terminal Block', 'part_no': 'TB-3P', 'cost': 35, 'lead_time': 3, 'supplier': 'Electrical Co.'},
                {'name': 'Cable Gland', 'part_no': 'CG-M20', 'cost': 12, 'lead_time': 2, 'supplier': 'Electrical Co.'},
                {'name': 'Contactor', 'part_no': 'CT-25A', 'cost': 85, 'lead_time': 7, 'supplier': 'ABB Distributors'},
                {'name': 'Overload Relay', 'part_no': 'OR-25', 'cost': 55, 'lead_time': 5, 'supplier': 'ABB Distributors'}
            ],
            'default': [
                {'name': 'Terminal Strip', 'part_no': 'TS-12', 'cost': 15, 'lead_time': 2, 'supplier': 'Electrical Co.'}
            ]
        },
        'shaft misalignment': {
            'motor': [
                {'name': 'Coupling Spider', 'part_no': 'CS-150', 'cost': 45, 'lead_time': 5, 'supplier': 'Coupling Co.'},
                {'name': 'Aligning Shims', 'part_no': 'AS-SET', 'cost': 30, 'lead_time': 2, 'supplier': 'Metal Works'},
                {'name': 'Foundation Bolt', 'part_no': 'FB-M20', 'cost': 8, 'lead_time': 2, 'supplier': 'Hardware Inc'}
            ],
            'default': [
                {'name': 'Coupling Element', 'part_no': 'CE-100', 'cost': 55, 'lead_time': 5, 'supplier': 'Coupling Co.'}
            ]
        },
        'lubrication failure': {
            'motor': [
                {'name': 'Bearing Housing Seal', 'part_no': 'BHS-6205', 'cost': 25, 'lead_time': 3, 'supplier': 'Seal Pro'},
                {'name': 'Lubricant (5L)', 'part_no': 'LUB-5L', 'cost': 80, 'lead_time': 2, 'supplier': 'Lubricant Inc'},
                {'name': 'Drain Plug', 'part_no': 'DP-M12', 'cost': 5, 'lead_time': 2, 'supplier': 'Hardware Inc'}
            ],
            'default': [
                {'name': 'Hydraulic Oil (20L)', 'part_no': 'HO-20', 'cost': 120, 'lead_time': 2, 'supplier': 'Lubricant Inc'},
                {'name': 'Grease Cartridge', 'part_no': 'GC-400', 'cost': 15, 'lead_time': 1, 'supplier': 'Lubricant Inc'}
            ]
        },
        'cooling system failure': {
            'motor': [
                {'name': 'Cooling Fan Motor', 'part_no': 'CFM-1HP', 'cost': 250, 'lead_time': 10, 'supplier': 'Fan Pro'},
                {'name': 'Thermostat', 'part_no': 'TH-100', 'cost': 45, 'lead_time': 5, 'supplier': 'Temperature Co.'},
                {'name': 'Coolant Pump', 'part_no': 'CP-50', 'cost': 180, 'lead_time': 14, 'supplier': 'Pump Parts'}
            ],
            'default': [
                {'name': 'Cooling Fan', 'part_no': 'CF-250', 'cost': 95, 'lead_time': 7, 'supplier': 'Fan Pro'}
            ]
        }
    }
    
    def recommend(
        self,
        equipment_name: str,
        equipment_type: str,
        root_cause: Optional[str] = None,
        failure_probability: Optional[float] = None,
        quantity_multiplier: int = 1
    ) -> SparePartSet:
        """
        Generate spare parts recommendations.
        
        Args:
            equipment_name: Name of equipment
            equipment_type: Type of equipment
            root_cause: Identified root cause
            failure_probability: Failure probability (0-1)
            quantity_multiplier: Multiplier for quantity (e.g., 2 for critical equipment)
            
        Returns:
            SparePartSet with all recommended parts
        """
        recommendation_id = str(uuid.uuid4())
        
        # Determine urgency based on failure probability
        if failure_probability and failure_probability >= 0.8:
            urgency = 'critical'
        elif failure_probability and failure_probability >= 0.6:
            urgency = 'high'
        elif root_cause:
            urgency = 'medium'
        else:
            urgency = 'low'
        
        # Get parts based on root cause and equipment type
        parts_data = self._get_parts_data(root_cause, equipment_type)
        
        # Create spare recommendations
        parts = []
        total_cost = 0
        critical = []
        
        for part_data in parts_data:
            qty = quantity_multiplier if urgency in ['critical', 'high'] else 1
            
            part = SpareRecommendation(
                part_id=str(uuid.uuid4()),
                part_name=part_data['name'],
                part_number=part_data['part_no'],
                quantity=qty,
                urgency=urgency,
                lead_time_days=part_data['lead_time'],
                estimated_cost=part_data['cost'] * qty,
                supplier=part_data.get('supplier'),
                reason=f"Required for {root_cause or 'maintenance'}",
                source="Spare Parts Database"
            )
            parts.append(part)
            total_cost += part.estimated_cost
            
            if urgency in ['critical', 'high']:
                critical.append(part.part_name)
        
        return SparePartSet(
            recommendation_id=recommendation_id,
            equipment_name=equipment_name,
            root_cause=root_cause or 'Unknown',
            timestamp=datetime.now(),
            parts=parts,
            total_estimated_cost=total_cost,
            critical_parts=critical
        )
    
    def _get_parts_data(
        self,
        root_cause: Optional[str],
        equipment_type: str
    ) -> List[Dict[str, Any]]:
        """Get parts data based on root cause and equipment type."""
        if not root_cause:
            return self.SPARE_PARTS_DB.get('default', {}).get('default', [])
        
        root_cause_lower = root_cause.lower()
        
        # Find matching root cause
        for cause_key, equipment_parts in self.SPARE_PARTS_DB.items():
            if cause_key in root_cause_lower:
                # Get parts for equipment type
                if equipment_type.lower() in equipment_parts:
                    return equipment_parts[equipment_type.lower()]
                elif 'default' in equipment_parts:
                    return equipment_parts['default']
        
        return []
    
    def get_standard_parts(self, equipment_type: str) -> List[SpareRecommendation]:
        """Get standard parts for equipment type."""
        standard_parts = {
            'motor': [
                {'name': 'Bearing 6205', 'part_no': 'BB-6205', 'cost': 45, 'lead_time': 5, 'supplier': 'Bearing Co.'},
                {'name': 'Gasket Set', 'part_no': 'GS-STD', 'cost': 25, 'lead_time': 2, 'supplier': 'Seal Pro'},
                {'name': 'Lubricant', 'part_no': 'LUB-1L', 'cost': 20, 'lead_time': 1, 'supplier': 'Lubricant Inc'}
            ],
            'pump': [
                {'name': 'Mechanical Seal', 'part_no': 'MS-STD', 'cost': 80, 'lead_time': 7, 'supplier': 'Seal Pro'},
                {'name': 'O-Ring Kit', 'part_no': 'ORK-STD', 'cost': 15, 'lead_time': 2, 'supplier': 'Seal Pro'},
                {'name': 'Gasket Sheet', 'part_no': 'GS-500', 'cost': 30, 'lead_time': 3, 'supplier': 'Industrial Supply'}
            ],
            'compressor': [
                {'name': 'Air Filter', 'part_no': 'AF-STD', 'cost': 45, 'lead_time': 3, 'supplier': 'Filter Co.'},
                {'name': 'Oil Filter', 'part_no': 'OF-STD', 'cost': 35, 'lead_time': 3, 'supplier': 'Filter Co.'},
                {'name': 'Compressor Oil', 'part_no': 'CO-5L', 'cost': 65, 'lead_time': 2, 'supplier': 'Lubricant Inc'}
            ]
        }
        
        parts_data = standard_parts.get(equipment_type.lower(), [])
        
        return [
            SpareRecommendation(
                part_id=str(uuid.uuid4()),
                part_name=p['name'],
                part_number=p['part_no'],
                quantity=1,
                urgency='medium',
                lead_time_days=p['lead_time'],
                estimated_cost=p['cost'],
                supplier=p.get('supplier'),
                reason="Standard maintenance part",
                source="Standard Parts Database"
            )
            for p in parts_data
        ]


# Singleton instance
_spare_recommender: Optional[SparePartRecommender] = None


def get_spare_recommender() -> SparePartRecommender:
    """Get global spare part recommender instance."""
    global _spare_recommender
    if _spare_recommender is None:
        _spare_recommender = SparePartRecommender()
    return _spare_recommender