from datetime import datetime, timezone
import re


def get_data_sensitivity_level(data_type: str) -> int:
    """Get sensitivity level for data type"""
    sensitivity_map = {
        "Patient.demographics": 1,
        "Observation.vital-signs": 1,
        "Observation.laboratory": 2,
        "DiagnosticReport.imaging": 2,
        "Condition.diagnosis": 3,
        "Condition.mental-health": 4,
        "MedicationRequest.controlled": 4,
        "AllergyIntolerance": 4,
        "Observation.genetic": 5
    }
    return sensitivity_map.get(data_type, 2)


def parse_datetime_safe(datetime_str: str) -> datetime:
    """
    Parse datetime string with proper timezone handling.
    Fixes the offset-naive vs offset-aware comparison issue.
    """
    if not datetime_str:
        return datetime.now(timezone.utc)

    try:
        # Handle Z timezone notation
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str.replace('Z', '+00:00')

        # Parse the datetime
        dt = datetime.fromisoformat(datetime_str)

        # If no timezone info, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    except (ValueError, TypeError) as e:
        print(f"Warning: Error parsing datetime '{datetime_str}': {e}")
        return datetime.now(timezone.utc)


def get_current_utc() -> datetime:
    """Get current UTC datetime with timezone awareness"""
    return datetime.now(timezone.utc)


def validate_patient_id_format(patient_id: str) -> bool:
    """Validate patient ID format (Kenyan National Health ID pattern)"""
    if not patient_id:
        return False
    # Pattern: CR followed by 9 digits
    return bool(re.match(r'^CR\d{9}$', patient_id))
