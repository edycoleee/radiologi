import os
from dotenv import load_dotenv
from flask import Flask, request
from flask_restx import Api, Resource, Namespace, fields
import requests
from datetime import datetime, timedelta


def create_app():
    # Load environment variables from .env (if present)
    load_dotenv()

    app = Flask(__name__)

    api = Api(
        app,
        version="1.1",
        title="Satu Sehat Gateway",
        doc="/api/docs",
        prefix="/api",
    )

    ns = Namespace("satset", description="Satu Sehat endpoints")

    # Swagger model for creating an Encounter via GUI (field-mode)
    encounter_input_model = api.model(
        "EncounterInput",
        {
            "identifier_value": fields.String(description="No register / identifier value", example="RG2023I0000175"),
            "subject_id": fields.String(description="Patient ID (will be prefixed with 'Patient/')", example="P10443013727"),
            "subject_reference": fields.String(description="Full subject reference (overrides subject_id)", example="Patient/P10443013727"),
            "subject_display": fields.String(description="Patient display name", example="MILA YASYFI TASBIHA"),
            "individual_id": fields.String(description="Practitioner ID (will be prefixed with 'Practitioner/')", example="10016869420"),
            "individual_reference": fields.String(description="Full practitioner reference (overrides individual_id)", example="Practitioner/10016869420"),
            "individual_display": fields.String(description="Practitioner display name", example="dr. ARIAWAN SETIADI, Sp.A"),
            "period_start": fields.String(description="Period start (ISO8601)", example="2025-08-01T05:57:41+00:00"),
            "period_end": fields.String(description="Period end (ISO8601). Optional — defaults to start + 10 minutes", example="2025-08-01T06:07:41+00:00"),
            "location_id": fields.String(description="Location ID (will be prefixed with 'Location/')", example="ecff1c64-3f62-4469-b577-ea38f263b276"),
            "location_reference": fields.String(description="Full location reference (overrides location_id)", example="Location/ecff1c64-3f62-4469-b577-ea38f263b276"),
            "location_display": fields.String(description="Location display name", example="Ruang 1, Poliklinik Anak, Lantai 1, Gedung Poliklinik"),
        },
    )

    # Swagger model for creating a ServiceRequest via GUI
    servicereq_input_model = api.model(
        "ServiceRequestInput",
        {
            "identifier_value": fields.String(description="No register / identifier value", example="RG2023I0000176"),
            "noacsn": fields.String(description="Accession Number (NOACSN)", example="20250002"),
            "subject_id": fields.String(description="Patient ID (will be prefixed with 'Patient/')", example="P10443013727"),
            "encounter_id": fields.String(description="Encounter ID (will be prefixed with 'Encounter/')", example="015aa41f-88d7-4b0b-b5f1-d511522bfa87"),
            "period_start": fields.String(description="Occurrence datetime (ISO8601)", example="2025-08-31T15:25:00+00:00"),
            "requester_reference": fields.String(description="Requester reference (e.g. Practitioner/10016869420)", example="Practitioner/10016869420"),
            "requester_display": fields.String(description="Requester display name", example="dr. ARIAWAN SETIADI, Sp.A"),
            "performer_reference": fields.String(description="Performer reference (e.g. Practitioner/10000504193)", example="Practitioner/10000504193"),
            "performer_display": fields.String(description="Performer display name", example="dr. RINI SUSANTI, Sp.Rad"),
        },
    )


    @ns.route("/halo")
    class Halo(Resource):
        def get(self):
            return {"message": "Halo dari Satu Sehat!"}, 200


    @ns.route("/token")
    class Token(Resource):
        def get(self):
            # Get parameters from query string, app config, or environment
            auth_url = (
                request.args.get("auth_url")
                or app.config.get("AUTH_URL")
                or os.getenv("AUTH_URL")
            )
            client_id = (
                request.args.get("client_id")
                or app.config.get("CLIENT_ID")
                or os.getenv("CLIENT_ID")
            )
            client_secret = (
                request.args.get("client_secret")
                or app.config.get("CLIENT_SECRET")
                or os.getenv("CLIENT_SECRET")
            )

            if not auth_url or not client_id or not client_secret:
                return {
                    "error": "Missing required parameters. Provide `auth_url`, `client_id`, and `client_secret` as query params or environment variables (AUTH_URL, CLIENT_ID, CLIENT_SECRET)."
                }, 400

            token_url = auth_url.rstrip("/") + "/accesstoken?grant_type=client_credentials"

            try:
                resp = requests.post(
                    token_url,
                    data={"client_id": client_id, "client_secret": client_secret},
                    timeout=15,
                )
            except requests.RequestException as exc:
                return {"error": "Failed to contact auth server", "detail": str(exc)}, 502

            # Try to forward JSON response when possible, otherwise return raw text
            content_type = resp.headers.get("Content-Type", "")
            try:
                if "application/json" in content_type:
                    return resp.json(), resp.status_code
                # some oauth servers return application/x-www-form-urlencoded or plain text
                try:
                    return resp.json(), resp.status_code
                except Exception:
                    return {"raw": resp.text}, resp.status_code
            except Exception as exc:
                return {"error": "Response parse error", "detail": str(exc)}, 500


    @ns.route("/encounter")
    @ns.expect(encounter_input_model, validate=False)
    class EncounterCreate(Resource):
        @ns.doc(description="Create an Encounter. You can either paste a full FHIR Encounter resource or fill the form fields below.")
        def post(self):
            """Create an Encounter resource on the remote FHIR server.

            Expected JSON body (either full FHIR Encounter resource or fields below):
            - identifier_value
            - subject_reference (e.g. "Patient/P10443013727") or subject_id (e.g. "P10443013727")
            - subject_display
            - individual_reference (e.g. "Practitioner/10016869420") or individual_id
            - individual_display
            - period_start (ISO8601)
            - period_end (ISO8601) optional (defaults to start + 10 minutes)
            - location_reference (e.g. "Location/ecff1c64-...") or location_id
            - location_display

            Authentication: uses env/base config `AUTH_URL`, `CLIENT_ID`, `CLIENT_SECRET`, and `BASE_URL`.
            If an `ACCESS_TOKEN` env var is present it will be used directly.
            """

            data = request.get_json(silent=True) or {}

            # If caller provided a full FHIR resource, forward it directly
            if isinstance(data, dict) and data.get("resourceType") == "Encounter":
                encounter = data
            else:
                identifier_value = data.get("identifier_value") or data.get("identifier")
                subject_ref = (
                    data.get("subject_reference")
                    or ("Patient/" + data.get("subject_id")) if data.get("subject_id") else None
                    or ("Patient/" + data.get("subject_patient")) if data.get("subject_patient") else None
                )
                subject_display = data.get("subject_display")
                individual_ref = (
                    data.get("individual_reference")
                    or ("Practitioner/" + data.get("individual_id")) if data.get("individual_id") else None
                    or ("Practitioner/" + data.get("individual_practitioner")) if data.get("individual_practitioner") else None
                )
                individual_display = data.get("individual_display")
                period_start = data.get("period_start")
                period_end = data.get("period_end")
                location_ref = (
                    data.get("location_reference")
                    or ("Location/" + data.get("location_id")) if data.get("location_id") else None
                    or ("Location/" + data.get("location")) if data.get("location") else None
                )
                location_display = data.get("location_display")

                if not period_start:
                    return {"error": "`period_start` is required when not providing a full Encounter resource."}, 400

                # compute period_end if not provided
                try:
                    dt_start = datetime.fromisoformat(period_start)
                except Exception:
                    return {"error": "`period_start` must be an ISO8601 datetime string."}, 400

                if not period_end:
                    dt_end = dt_start + timedelta(minutes=10)
                    period_end = dt_end.isoformat()

                encounter = {
                    "resourceType": "Encounter",
                    "identifier": [
                        {
                            "system": f"http://sys-ids.kemkes.go.id/encounter/{os.getenv('ORG_ID')}",
                            "value": identifier_value,
                        }
                    ],
                    "status": "arrived",
                    "class": {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "AMB",
                        "display": "ambulatory",
                    },
                    "subject": {
                        "reference": subject_ref,
                        "display": subject_display,
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
                            "individual": {"reference": individual_ref, "display": individual_display},
                        }
                    ],
                    "period": {"start": period_start, "end": period_end},
                    "location": [{"location": {"reference": location_ref, "display": location_display}}],
                    "statusHistory": [
                        {
                            "status": "arrived",
                            "period": {"start": period_start, "end": period_end},
                        }
                    ],
                    "serviceProvider": {"reference": f"Organization/{os.getenv('ORG_ID')}"},
                }

            # Resolve auth and base URLs
            auth_url = (
                request.args.get("auth_url") or app.config.get("AUTH_URL") or os.getenv("AUTH_URL")
            )
            client_id = (
                request.args.get("client_id") or app.config.get("CLIENT_ID") or os.getenv("CLIENT_ID")
            )
            client_secret = (
                request.args.get("client_secret") or app.config.get("CLIENT_SECRET") or os.getenv("CLIENT_SECRET")
            )
            base_url = (
                request.args.get("base_url") or app.config.get("BASE_URL") or os.getenv("BASE_URL")
            )

            if not base_url:
                return {"error": "Missing BASE_URL (provide as env BASE_URL or query param `base_url`)"}, 400

            # Try to use an existing ACCESS_TOKEN env var first
            access_token = os.getenv("ACCESS_TOKEN")

            if not access_token:
                if not auth_url or not client_id or not client_secret:
                    return {
                        "error": "Missing auth params. Set AUTH_URL, CLIENT_ID, CLIENT_SECRET in env or pass as query params."
                    }, 400

                token_url = auth_url.rstrip("/") + "/accesstoken?grant_type=client_credentials"
                try:
                    tresp = requests.post(
                        token_url,
                        data={"client_id": client_id, "client_secret": client_secret},
                        timeout=15,
                    )
                except requests.RequestException as exc:
                    return {"error": "Failed to contact auth server", "detail": str(exc)}, 502

                try:
                    tjson = tresp.json()
                except Exception:
                    return {"error": "Invalid token response", "detail": tresp.text}, 502

                access_token = tjson.get("access_token") or tjson.get("accessToken") or tjson.get("token")
                if not access_token:
                    return {"error": "No access token in auth response", "detail": tjson}, 502

            # Send Encounter to FHIR server
            encounter_url = base_url.rstrip("/") + "/Encounter"
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/fhir+json"}

            try:
                fresp = requests.post(encounter_url, json=encounter, headers=headers, timeout=20)
            except requests.RequestException as exc:
                return {"error": "Failed to POST Encounter", "detail": str(exc)}, 502

            ctype = fresp.headers.get("Content-Type", "")
            try:
                if "application/json" in ctype or "+json" in ctype:
                    return fresp.json(), fresp.status_code
                else:
                    return {"raw": fresp.text}, fresp.status_code
            except Exception:
                return {"raw": fresp.text}, fresp.status_code


    @ns.route("/service-req")
    @ns.expect(servicereq_input_model, validate=False)
    class ServiceRequestCreate(Resource):
        @ns.doc(description="Create a ServiceRequest. You can paste a full FHIR ServiceRequest resource or fill the form fields below.")
        def post(self):
            data = request.get_json(silent=True) or {}

            # If caller provided a full FHIR resource, forward it directly
            if isinstance(data, dict) and data.get("resourceType") == "ServiceRequest":
                sreq = data
            else:
                identifier_value = data.get("identifier_value")
                noacsn = data.get("noacsn")
                subject_id = data.get("subject_id")
                encounter_id = data.get("encounter_id")
                period_start = data.get("period_start")
                requester_reference = data.get("requester_reference")
                requester_display = data.get("requester_display")
                performer_reference = data.get("performer_reference")
                performer_display = data.get("performer_display")

                # basic validation
                if not identifier_value or not noacsn or not subject_id or not encounter_id or not period_start:
                    return {"error": "Missing required fields: identifier_value, noacsn, subject_id, encounter_id, period_start"}, 400

                # build ServiceRequest resource
                sreq = {
                    "resourceType": "ServiceRequest",
                    "identifier": [
                        {
                            "system": f"http://sys-ids.kemkes.go.id/servicerequest/{os.getenv('ORG_ID')}",
                            "value": identifier_value,
                        },
                        {
                            "use": "usual",
                            "type": {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                        "code": "ACSN",
                                    }
                                ]
                            },
                            "system": f"http://sys-ids.kemkes.go.id/acsn/{os.getenv('ORG_ID')}",
                            "value": noacsn,
                        },
                    ],
                    "status": "active",
                    "intent": "original-order",
                    "priority": "routine",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "363679005",
                                    "display": "Imaging",
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "79103-8",
                                "display": "CT Abdomen W contrast IV",
                            }
                        ],
                        "text": "Pemeriksaan CT Scan Abdomen Atas",
                    },
                    "subject": {"reference": f"Patient/{subject_id}"},
                    "encounter": {"reference": f"Encounter/{encounter_id}"},
                    "occurrenceDateTime": period_start,
                    "authoredOn": period_start,
                    "requester": {"reference": requester_reference, "display": requester_display},
                    "performer": [{"reference": performer_reference, "display": performer_display}],
                    "bodySite": [
                        {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "80581009",
                                    "display": "Upper abdomen structure",
                                }
                            ]
                        }
                    ],
                    "reasonCode": [{"text": "Periksa risiko adanya sumbatan batu empedu"}],
                }

            # resolve base url and auth same as other endpoints
            auth_url = (
                request.args.get("auth_url") or app.config.get("AUTH_URL") or os.getenv("AUTH_URL")
            )
            client_id = (
                request.args.get("client_id") or app.config.get("CLIENT_ID") or os.getenv("CLIENT_ID")
            )
            client_secret = (
                request.args.get("client_secret") or app.config.get("CLIENT_SECRET") or os.getenv("CLIENT_SECRET")
            )
            base_url = (
                request.args.get("base_url") or app.config.get("BASE_URL") or os.getenv("BASE_URL")
            )

            if not base_url:
                return {"error": "Missing BASE_URL (provide as env BASE_URL or query param `base_url`)"}, 400

            access_token = os.getenv("ACCESS_TOKEN")
            if not access_token:
                if not auth_url or not client_id or not client_secret:
                    return {"error": "Missing auth params. Set AUTH_URL, CLIENT_ID, CLIENT_SECRET in env or pass as query params."}, 400
                token_url = auth_url.rstrip("/") + "/accesstoken?grant_type=client_credentials"
                try:
                    tresp = requests.post(token_url, data={"client_id": client_id, "client_secret": client_secret}, timeout=15)
                except requests.RequestException as exc:
                    return {"error": "Failed to contact auth server", "detail": str(exc)}, 502
                try:
                    tjson = tresp.json()
                except Exception:
                    return {"error": "Invalid token response", "detail": tresp.text}, 502
                access_token = tjson.get("access_token") or tjson.get("accessToken") or tjson.get("token")
                if not access_token:
                    return {"error": "No access token in auth response", "detail": tjson}, 502

            # send ServiceRequest to FHIR server
            sreq_url = base_url.rstrip("/") + "/ServiceRequest"
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/fhir+json"}
            try:
                sresp = requests.post(sreq_url, json=sreq, headers=headers, timeout=20)
            except requests.RequestException as exc:
                return {"error": "Failed to POST ServiceRequest", "detail": str(exc)}, 502

            ctype = sresp.headers.get("Content-Type", "")
            try:
                if "application/json" in ctype or "+json" in ctype:
                    return sresp.json(), sresp.status_code
                else:
                    return {"raw": sresp.text}, sresp.status_code
            except Exception:
                return {"raw": sresp.text}, sresp.status_code


    api.add_namespace(ns)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
