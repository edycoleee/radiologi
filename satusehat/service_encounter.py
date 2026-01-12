from datetime import datetime, timedelta
from config import Config

def build_encounter_resource(data):
    if data.get("resourceType") == "Encounter":
        return data

    period_start = data.get("period_start")
    if not period_start:
        raise ValueError("period_start is required")

    try:
        dt_start = datetime.fromisoformat(period_start)
    except:
        raise ValueError("period_start must be ISO8601")

    period_end = data.get("period_end") or (dt_start + timedelta(minutes=10)).isoformat()

    org_id = Config.SS_ORG_ID

    return {
        "resourceType": "Encounter",
        "identifier": [
            {
                "system": f"http://sys-ids.kemkes.go.id/encounter/{org_id}",
                "value": data.get("identifier_value"),
            }
        ],
        "status": "arrived",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        "subject": {
            "reference": data.get("subject_reference") or f"Patient/{data.get('subject_id')}",
            "display": data.get("subject_display"),
        },
        "participant": [
            {
                "type": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": "ATND",
                                "display": "attender",
                            }
                        ]
                    }
                ],
                "individual": {
                    "reference": data.get("individual_reference") or f"Practitioner/{data.get('individual_id')}",
                    "display": data.get("individual_display"),
                },
            }
        ],
        "period": {"start": period_start, "end": period_end},
        "location": [
            {
                "location": {
                    "reference": data.get("location_reference") or f"Location/{data.get('location_id')}",
                    "display": data.get("location_display"),
                }
            }
        ],
        "statusHistory": [{"status": "arrived", "period": {"start": period_start, "end": period_end}}],
        "serviceProvider": {"reference": f"Organization/{org_id}"},
    }
