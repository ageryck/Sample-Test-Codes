from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from .consent_decision_type import ConsentDecisionType

@dataclass
class ConsentDecision:
    """Consent validation decision"""
    decision: ConsentDecisionType
    reason: str
    permissions: Dict[str, Any] = field(default_factory=dict)
    access_token: Optional[str] = None
    expiry_time: Optional[Any] = None
    restrictions: List[str] = field(default_factory=list)
    audit_info: Dict[str, Any] = field(default_factory=dict) 