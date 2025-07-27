from enum import Enum

class ConsentStatus(Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    ACTIVE = "active"
    REJECTED = "rejected"
    INACTIVE = "inactive"
    ENTERED_IN_ERROR = "entered-in-error" 