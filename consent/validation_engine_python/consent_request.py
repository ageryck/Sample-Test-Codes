from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

@dataclass
class ConsentRequest:
    """Incoming consent request structure"""
    request_id: str
    patient_id: str
    requester_id: str
    requester_organization: str
    requester_role: str
    data_types: List[str]
    purpose: str
    time_range: Dict[str, str]
    emergency_context: bool = False
    timestamp: datetime = field(default_factory=datetime.now) 