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

    # Swagger model for creating an Observation via GUI (field-mode)
    observation_input_model = api.model(
        "ObservationInput",
        {
            "identifier_value": fields.String(description="No register / identifier value", example="RG2023I0000174"),
            "codind_code": fields.String(description="LOINC or code for the observation (accepts codind_code typo)", example="24648-8"),
            "coding_code": fields.String(description="Coding code (alternative)", example="24648-8"),
            "coding_display": fields.String(description="Coding display text", example="XR Chest PA upright"),
            "subject_id": fields.String(description="Patient ID", example="P10443013727"),
            "subject_display": fields.String(description="Patient display name", example="MILA YASYFI TASBIHA"),
            "encounter_id": fields.String(description="Encounter ID", example="6dc2dc13-0b5a-4105-996e-6403e43be60a"),
            "period_start": fields.String(description="Effective datetime (ISO8601)", example="2025-08-31T15:25:00+00:00"),
            "performer_id": fields.String(description="Performer Practitioner ID", example="10000504193"),
            "performer_display": fields.String(description="Performer display name", example="dr. RINI SUSANTI, Sp.Rad"),
            "performer_value": fields.String(description="Observation textual value/result", example="Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru"),
            "service_request_id": fields.String(description="Related ServiceRequest ID", example="a33163ec-ba77-4775-8d20-83035b76e668"),
            "imaging_study_id": fields.String(description="Related ImagingStudy ID", example="75b7e9d0-c079-419c-84f8-8dba7b9cd585"),
        },
    )

    # Swagger model for creating a DiagnosticReport (conclusion)
    diagnostic_input_model = api.model(
        "DiagnosticReportInput",
        {
            "identifier_value": fields.String(description="No register / identifier value", example="RG2023I0000174"),
            "codind_code": fields.String(description="LOINC or code for the report (accepts codind_code typo)", example="24648-8"),
            "coding_display": fields.String(description="Coding display text", example="XR Chest PA upright"),
            "subject_id": fields.String(description="Patient ID", example="P10443013727"),
            "encounter_id": fields.String(description="Encounter ID", example="6dc2dc13-0b5a-4105-996e-6403e43be60a"),
            "period_start": fields.String(description="Effective datetime (ISO8601)", example="2025-08-31T15:25:00+00:00"),
            "performer_id": fields.String(description="Performer Practitioner ID", example="10000504193"),
            "imaging_study_id": fields.String(description="ImagingStudy ID", example="75b7e9d0-c079-419c-84f8-8dba7b9cd585"),
            "observation_id": fields.String(description="Observation ID", example="82b9af58-c98d-4263-9a6f-9a04fdfec43a"),
            "service_request_id": fields.String(description="Related ServiceRequest ID", example="a33163ec-ba77-4775-8d20-83035b76e668"),
            "conclusion_text": fields.String(description="Conclusion text", example="Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru"),
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
            """

            data = request.get_json(silent=True) or {}

            # If caller provided a full FHIR resource, forward it directly
            if isinstance(data, dict) and data.get("resourceType") == "Encounter":
                encounter = data
            else:
                # Accept multiple possible field names coming from different clients
                identifier_value = (
                    data.get("identifier_value")
                    or data.get("identifier")
                    or data.get("identifier_id")
                )

                # Subject may be provided as full reference or id
                subject_ref = (
                    data.get("subject_reference")
                    or ("Patient/" + data.get("subject_id") if data.get("subject_id") else None)
                    or ("Patient/" + data.get("subject_patient") if data.get("subject_patient") else None)
                )
                subject_display = data.get("subject_display")

                # Practitioner / participant fields: support both `individual_*` and `practitioner_*` names
                individual_ref = (
                    data.get("individual_reference")
                    or ("Practitioner/" + data.get("individual_id") if data.get("individual_id") else None)
                    or ("Practitioner/" + data.get("individual_practitioner") if data.get("individual_practitioner") else None)
                    or data.get("practitioner_reference")
                    or ("Practitioner/" + data.get("practitioner_id") if data.get("practitioner_id") else None)
                )
                individual_display = (
                    data.get("individual_display") or data.get("practitioner_name") or data.get("practitioner_display")
                )

                period_start = data.get("period_start")
                period_end = data.get("period_end")

                location_ref = (
                    data.get("location_reference")
                    or ("Location/" + data.get("location_id") if data.get("location_id") else None)
                    or ("Location/" + data.get("location") if data.get("location") else None)
                )
                location_display = data.get("location_display")

                # allow caller to override org id used in identifier/serviceProvider
                body_org_id = data.get("org_id") or data.get("organization_id") or os.getenv("ORG_ID")

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
                            "system": f"http://sys-ids.kemkes.go.id/encounter/{body_org_id}",
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
                    "serviceProvider": {"reference": f"Organization/{body_org_id}"},
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

                # requester/performer: support both `requester_*` and `practitioner_*` fields
                requester_reference = (
                    data.get("requester_reference")
                    or ("Practitioner/" + data.get("practitioner_id") if data.get("practitioner_id") else None)
                )
                requester_display = data.get("requester_display") or data.get("practitioner_name")

                performer_reference = (
                    data.get("performer_reference")
                    or ("Practitioner/" + data.get("performer_id") if data.get("performer_id") else None)
                )
                performer_display = data.get("performer_display") or data.get("performer_name")

                # coding for requested service: accept either `codind_code` (typo) or `coding_code`
                coding_code = data.get("codind_code") or data.get("coding_code") or data.get("code")
                coding_display = data.get("coding_display") or data.get("codingText") or data.get("code_display")

                # allow caller to override org id used in identifier/serviceProvider
                body_org_id = data.get("org_id") or data.get("organization_id") or os.getenv("ORG_ID")

                # basic validation
                if not identifier_value or not noacsn or not subject_id or not encounter_id or not period_start:
                    return {"error": "Missing required fields: identifier_value, noacsn, subject_id, encounter_id, period_start"}, 400

                # default coding if not provided
                code_entry = {
                    "system": "http://loinc.org",
                    "code": coding_code or "79103-8",
                    "display": coding_display or "CT Abdomen W contrast IV",
                }

                text_display = coding_display or "Pemeriksaan CT Scan Abdomen Atas"

                # build ServiceRequest resource
                sreq = {
                    "resourceType": "ServiceRequest",
                    "identifier": [
                        {
                            "system": f"http://sys-ids.kemkes.go.id/servicerequest/{body_org_id}",
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
                            "system": f"http://sys-ids.kemkes.go.id/acsn/{body_org_id}",
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
                        "coding": [code_entry],
                        "text": text_display,
                    },
                    "orderDetail": [
                        {
                            "coding": [
                                {
                                    "system": "http://dicom.nema.org/resources/ontology/DCM",
                                    "code": "DX",
                                }
                            ],
                            "text": "Modality Code: DX",
                        },
                        {
                            "coding": [
                                {
                                    "system": "http://sys-ids.kemkes.go.id/ae-title",
                                    "display": "DX0001",
                                }
                            ]
                        }
                    ],
                    "subject": {"reference": f"Patient/{subject_id}"},
                    "encounter": {"reference": f"Encounter/{encounter_id}", "display": f"Permintaan pemeriksaan {text_display}"},
                    "occurrenceDateTime": period_start,
                    "authoredOn": period_start,
                    "requester": {"reference": requester_reference, "display": requester_display},
                    "performer": [{"reference": performer_reference, "display": performer_display}],
                    "reasonCode": [{"text": "Periksa rutin"}],
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


    @ns.route("/imageid/<string:acsn>")
    class ImageId(Resource):
        def get(self, acsn):
            """Lookup ImagingStudy by ACSN and return the ImagingStudy id."""
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
            org_id = request.args.get("org_id") or os.getenv("ORG_ID")

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

            # build ImagingStudy search URL
            identifier_system = f"http://sys-ids.kemkes.go.id/acsn/{org_id}"
            imaging_url = f"{base_url.rstrip('/')}" + f"/ImagingStudy?identifier={identifier_system}|{acsn}"
            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/fhir+json"}

            try:
                resp = requests.get(imaging_url, headers=headers, timeout=20)
            except requests.RequestException as exc:
                return {"error": "Failed to GET ImagingStudy", "detail": str(exc)}, 502

            ctype = resp.headers.get("Content-Type", "")
            try:
                if "application/json" in ctype or "+json" in ctype:
                    j = resp.json()
                    # If server returned a Bundle, extract first ImagingStudy id
                    if isinstance(j, dict) and j.get("resourceType") == "Bundle":
                        entries = j.get("entry") or []
                        if not entries:
                            return {"error": "No ImagingStudy found", "detail": j}, 404
                        for e in entries:
                            res = e.get("resource") or {}
                            if res.get("resourceType") == "ImagingStudy" and res.get("id"):
                                return {"imagingStudy_id": res.get("id")}, 200
                        first = entries[0].get("resource") or {}
                        if first.get("id"):
                            return {"imagingStudy_id": first.get("id")}, 200
                        return {"error": "No ImagingStudy id in results", "detail": j}, 502
                    # If single ImagingStudy returned
                    if isinstance(j, dict) and j.get("resourceType") == "ImagingStudy":
                        return {"imagingStudy_id": j.get("id")}, 200
                    return j, resp.status_code
                else:
                    return {"raw": resp.text}, resp.status_code
            except Exception:
                return {"raw": resp.text}, resp.status_code


    @ns.route("/observation")
    @ns.expect(observation_input_model, validate=False)
    class ObservationCreate(Resource):
        def post(self):
            data = request.get_json(silent=True) or {}

            # Allow passing a full Observation resource
            if isinstance(data, dict) and data.get("resourceType") == "Observation":
                obs = data
            else:
                identifier_value = data.get("identifier_value") or data.get("identifier")
                coding_code = data.get("codind_code") or data.get("coding_code") or data.get("code")
                coding_display = data.get("coding_display") or data.get("codingText")
                subject_id = data.get("subject_id")
                subject_display = data.get("subject_display")
                encounter_id = data.get("encounter_id")
                period_start = data.get("period_start")
                performer_id = data.get("performer_id")
                performer_display = data.get("performer_display")
                performer_value = data.get("performer_value") or data.get("valueString")
                service_request_id = data.get("service_request_id") or data.get("ServiceRequest_id")
                imaging_study_id = data.get("imaging_study_id") or data.get("ImagingStudy_id")

                body_org_id = data.get("org_id") or data.get("organization_id") or os.getenv("ORG_ID")

                # basic validation
                if not identifier_value or not subject_id or not encounter_id or not period_start:
                    return {"error": "Missing required fields: identifier_value, subject_id, encounter_id, period_start"}, 400

                code_entry = {
                    "system": "http://loinc.org",
                    "code": coding_code or "79103-8",
                    "display": coding_display or "Imaging result",
                }

                obs = {
                    "resourceType": "Observation",
                    "identifier": [
                        {
                            "system": f"http://sys-ids.kemkes.go.id/observation/{body_org_id}",
                            "value": identifier_value,
                        }
                    ],
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "imaging",
                                    "display": "Imaging",
                                }
                            ]
                        }
                    ],
                    "code": {"coding": [code_entry]},
                    "subject": {"reference": f"Patient/{subject_id}", "display": subject_display},
                    "encounter": {"reference": f"Encounter/{encounter_id}"},
                    "effectiveDateTime": period_start,
                    "issued": period_start,
                    "performer": [{"reference": f"Practitioner/{performer_id}", "display": performer_display}],
                    "valueString": performer_value,
                    "basedOn": [{"reference": f"ServiceRequest/{service_request_id}"}] if service_request_id else [],
                    "derivedFrom": [{"reference": f"ImagingStudy/{imaging_study_id}"}] if imaging_study_id else [],
                }

            # resolve auth/base
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

            obs_url = base_url.rstrip("/") + "/Observation"
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/fhir+json"}
            try:
                oresp = requests.post(obs_url, json=obs, headers=headers, timeout=20)
            except requests.RequestException as exc:
                return {"error": "Failed to POST Observation", "detail": str(exc)}, 502

            ctype = oresp.headers.get("Content-Type", "")
            try:
                if "application/json" in ctype or "+json" in ctype:
                    return oresp.json(), oresp.status_code
                else:
                    return {"raw": oresp.text}, oresp.status_code
            except Exception:
                return {"raw": oresp.text}, oresp.status_code


    @ns.route("/conclusion")
    @ns.expect(diagnostic_input_model, validate=False)
    class DiagnosticCreate(Resource):
        def post(self):
            data = request.get_json(silent=True) or {}

            # Accept a full DiagnosticReport resource
            if isinstance(data, dict) and data.get("resourceType") == "DiagnosticReport":
                drep = data
            else:
                identifier_value = data.get("identifier_value") or data.get("identifier")
                coding_code = data.get("codind_code") or data.get("coding_code") or data.get("code")
                coding_display = data.get("coding_display") or data.get("codingText")
                subject_id = data.get("subject_id")
                encounter_id = data.get("encounter_id")
                period_start = data.get("period_start")
                performer_id = data.get("performer_id")
                imaging_study_id = data.get("imaging_study_id")
                observation_id = data.get("observation_id") or data.get("ObservationId")
                service_request_id = data.get("service_request_id")
                conclusion_text = data.get("conclusion_text") or data.get("conclusion")

                body_org_id = data.get("org_id") or data.get("organization_id") or os.getenv("ORG_ID")

                # basic validation
                if not identifier_value or not subject_id or not encounter_id or not period_start:
                    return {"error": "Missing required fields: identifier_value, subject_id, encounter_id, period_start"}, 400

                code_entry = {
                    "system": "http://loinc.org",
                    "code": coding_code or "79103-8",
                    "display": coding_display or "Imaging",
                }

                drep = {
                    "resourceType": "DiagnosticReport",
                    "identifier": [
                        {
                            "system": f"http://sys-ids.kemkes.go.id/diagnostic/{body_org_id}/rad",
                            "use": "official",
                            "value": identifier_value,
                        }
                    ],
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                                    "code": "RAD",
                                    "display": "Radiology",
                                }
                            ]
                        }
                    ],
                    "code": {"coding": [code_entry]},
                    "subject": {"reference": f"Patient/{subject_id}"},
                    "encounter": {"reference": f"Encounter/{encounter_id}"},
                    "effectiveDateTime": period_start,
                    "issued": period_start,
                    "performer": [
                        {"reference": f"Practitioner/{performer_id}"},
                        {"reference": f"Organization/{body_org_id}"},
                    ],
                    "imagingStudy": [{"reference": f"ImagingStudy/{imaging_study_id}"}] if imaging_study_id else [],
                    "result": [{"reference": f"Observation/{observation_id}"}] if observation_id else [],
                    "basedOn": [{"reference": f"ServiceRequest/{service_request_id}"}] if service_request_id else [],
                    "conclusion": conclusion_text or "",
                }

            # resolve auth/base
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

            drep_url = base_url.rstrip("/") + "/DiagnosticReport"
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/fhir+json"}
            try:
                dresp = requests.post(drep_url, json=drep, headers=headers, timeout=20)
            except requests.RequestException as exc:
                return {"error": "Failed to POST DiagnosticReport", "detail": str(exc)}, 502

            ctype = dresp.headers.get("Content-Type", "")
            try:
                if "application/json" in ctype or "+json" in ctype:
                    return dresp.json(), dresp.status_code
                else:
                    return {"raw": dresp.text}, dresp.status_code
            except Exception:
                return {"raw": dresp.text}, dresp.status_code

    api.add_namespace(ns)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5000)