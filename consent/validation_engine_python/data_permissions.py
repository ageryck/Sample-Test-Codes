from dataclasses import dataclass, field
from typing import List

@dataclass
class DataPermissions:
    """Granular data permissions"""
    allowed: List[str] = field(default_factory=list)
    denied: List[str] = field(default_factory=list)
    masked: List[str] = field(default_factory=list)
    pseudonymized: List[str] = field(default_factory=list) 