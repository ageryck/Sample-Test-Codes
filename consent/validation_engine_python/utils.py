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
    return sensitivity_map.get(data_type, 2)  # Default to medium sensitivity 