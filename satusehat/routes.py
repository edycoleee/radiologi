from flask import request
from flask_restx import Namespace, Resource, fields
from .service_encounter import build_encounter_resource
from .service_servicereq import build_servicereq_resource
from .service_observation import build_observation_resource
from .service_diagnostic import build_diagnostic_resource
from .service_imaging import lookup_imaging_by_acsn
from common.auth import get_access_token
from common.fhir_client import post_fhir
from config import Config
from .service_batch1 import process_batch1
from .service_batch2 import process_batch2
from .service_batch3 import process_batch3
from .service_batch4 import process_batch4
from .service_dicom import process_dicom



ns = Namespace("satset", description="Satu Sehat endpoints") 
dicom_ns = Namespace("dicom", description="DICOM Router / PACS Processing")


# -------------------------------
# Swagger Models
# -------------------------------
encounter_input = ns.model(
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

servicereq_input = ns.model(
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

batch1_input = ns.model(
    "Batch1Input",
    {
        "identifier_value": fields.String(description="No register", example="RG2023I0000175"),

        # Encounter fields
        "subject_id": fields.String(example="P10443013727"),
        "subject_reference": fields.String(example="Patient/P10443013727"),
        "subject_display": fields.String(example="MILA YASYFI TASBIHA"),
        "individual_id": fields.String(example="10016869420"),
        "individual_reference": fields.String(example="Practitioner/10016869420"),
        "individual_display": fields.String(example="dr. ARIAWAN SETIADI, Sp.A"),
        "period_start": fields.String(example="2025-08-01T05:57:41+00:00"),
        "period_end": fields.String(example="2025-08-01T06:07:41+00:00"),
        "location_id": fields.String(example="ecff1c64-3f62-4469-b577-ea38f263b276"),
        "location_reference": fields.String(example="Location/ecff1c64-3f62-4469-b577-ea38f263b276"),
        "location_display": fields.String(example="Ruang 1, Poliklinik Anak"),

        # ServiceRequest fields
        "noacsn": fields.String(example="20250002"),
        "requester_reference": fields.String(example="Practitioner/10016869420"),
        "requester_display": fields.String(example="dr. ARIAWAN SETIADI, Sp.A"),
        "performer_reference": fields.String(example="Practitioner/10000504193"),
        "performer_display": fields.String(example="dr. RINI SUSANTI, Sp.Rad"),
    },
)

observation_input = ns.model(
    "ObservationInput",
    {
        "identifier_value": fields.String(example="RG2023I0000174"),
        "codind_code": fields.String(example="24648-8"),
        "coding_display": fields.String(example="XR Chest PA upright"),

        "subject_id": fields.String(example="P10443013727"),
        "subject_display": fields.String(example="MILA YASYFI TASBIHA"),

        "encounter_id": fields.String(example="6dc2dc13-0b5a-4105-996e-6403e43be60a"),
        "period_start": fields.String(example="2025-08-31T15:25:00+00:00"),

        "performer_id": fields.String(example="10000504193"),
        "performer_display": fields.String(example="dr. RINI SUSANTI, Sp.Rad"),
        "performer_value": fields.String(example="Hasil Bacaan adalah ..."),

        "service_request_id": fields.String(example="a33163ec-ba77-4775-8d20-83035b76e668"),
        "imaging_study_id": fields.String(example="75b7e9d0-c079-419c-84f8-8dba7b9cd585"),
    },
)

diagnostic_input = ns.model(
    "DiagnosticReportInput",
    {
        "identifier_value": fields.String(example="RG2023I0000174"),
        "codind_code": fields.String(example="24648-8"),
        "coding_display": fields.String(example="XR Chest PA upright"),

        "subject_id": fields.String(example="P10443013727"),
        "encounter_id": fields.String(example="6dc2dc13-0b5a-4105-996e-6403e43be60a"),
        "period_start": fields.String(example="2025-08-31T15:25:00+00:00"),

        "performer_id": fields.String(example="10000504193"),

        "imaging_study_id": fields.String(example="75b7e9d0-c079-419c-84f8-8dba7b9cd585"),
        "observation_id": fields.String(example="82b9af58-c98d-4263-9a6f-9a04fdfec43a"),
        "service_request_id": fields.String(example="a33163ec-ba77-4775-8d20-83035b76e668"),

        "conclusion_text": fields.String(example="Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru"),
    },
)


batch2_input = ns.model(
    "Batch2Input",
    {
        "identifier_value": fields.String(example="RG2023I0000174"),

        "codind_code": fields.String(example="24648-8"),
        "coding_display": fields.String(example="XR Chest PA upright"),

        "subject_id": fields.String(example="P10443013727"),
        "subject_display": fields.String(example="MILA YASYFI TASBIHA"),

        "encounter_id": fields.String(example="6dc2dc13-0b5a-4105-996e-6403e43be60a"),
        "period_start": fields.String(example="2025-08-31T15:25:00+00:00"),

        "performer_id": fields.String(example="10000504193"),
        "performer_display": fields.String(example="dr. RINI SUSANTI, Sp.Rad"),
        "performer_value": fields.String(example="Hasil Bacaan adalah ..."),

        "service_request_id": fields.String(example="a33163ec-ba77-4775-8d20-83035b76e668"),
        "imaging_study_id": fields.String(example="75b7e9d0-c079-419c-84f8-8dba7b9cd585"),

        "conclusion_text": fields.String(example="Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru"),
    },
)

batch3_input = ns.model(
    "Batch3Input",
    {
        "identifier_value": fields.String(example="RG2023I0000175"),

        # Encounter
        "subject_id": fields.String(example="P10443013727"),
        "subject_reference": fields.String(example="Patient/P10443013727"),
        "subject_display": fields.String(example="MILA YASYFI TASBIHA"),
        "individual_id": fields.String(example="10016869420"),
        "individual_reference": fields.String(example="Practitioner/10016869420"),
        "individual_display": fields.String(example="dr. ARIAWAN SETIADI, Sp.A"),
        "period_start": fields.String(example="2025-08-01T05:57:41+00:00"),
        "period_end": fields.String(example="2025-08-01T06:07:41+00:00"),
        "location_id": fields.String(example="ecff1c64-3f62-4469-b577-ea38f263b276"),
        "location_reference": fields.String(example="Location/ecff1c64-3f62-4469-b577-ea38f263b276"),
        "location_display": fields.String(example="Ruang 1, Poliklinik Anak"),

        # ServiceRequest
        "noacsn": fields.String(example="20250002"),
        "requester_reference": fields.String(example="Practitioner/10016869420"),
        "requester_display": fields.String(example="dr. ARIAWAN SETIADI, Sp.A"),

        "performer_id": fields.String(example="10000504193"),
        "performer_reference": fields.String(example="Practitioner/10000504193"),
        "performer_display": fields.String(example="dr. RINI SUSANTI, Sp.Rad"),

        "codind_code": fields.String(example="24648-8"),
        "coding_display": fields.String(example="XR Chest PA upright"),

        # Observation
        "performer_value": fields.String(example="Hasil Bacaan adalah ..."),

        # ImagingStudy (lookup by ACSN)
        "imaging_study_id": fields.String(example="75b7e9d0-c079-419c-84f8-8dba7b9cd585"),

        # DiagnosticReport
        "conclusion_text": fields.String(example="Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru"),
    },
)

dicom_model = dicom_ns.model(
    "DicomProcessInput",
    {
        "study": fields.String(required=True, example="1.2.840.113619.2.55.3.604688433.783.159975"),
        "patientid": fields.String(example="P10443013727"),
        "accesionnum": fields.String(example="20250002"),
    },
)

batch4_input = ns.model(
    "Batch4Input",
    {
        "identifier_value": fields.String(example="RG2023I0000175"),

        # Encounter
        "subject_id": fields.String(example="P10443013727"),
        "subject_reference": fields.String(example="Patient/P10443013727"),
        "subject_display": fields.String(example="MILA YASYFI TASBIHA"),
        "individual_id": fields.String(example="10016869420"),
        "individual_reference": fields.String(example="Practitioner/10016869420"),
        "individual_display": fields.String(example="dr. ARIAWAN SETIADI, Sp.A"),
        "period_start": fields.String(example="2025-08-01T05:57:41+00:00"),
        "period_end": fields.String(example="2025-08-01T06:07:41+00:00"),
        "location_id": fields.String(example="ecff1c64-3f62-4469-b577-ea38f263b276"),
        "location_reference": fields.String(example="Location/ecff1c64-3f62-4469-b577-ea38f263b276"),
        "location_display": fields.String(example="Ruang 1, Poliklinik Anak"),

        # ServiceRequest
        "noacsn": fields.String(example="20250002"),
        "requester_reference": fields.String(example="Practitioner/10016869420"),
        "requester_display": fields.String(example="dr. ARIAWAN SETIADI, Sp.A"),

        "performer_id": fields.String(example="10000504193"),
        "performer_reference": fields.String(example="Practitioner/10000504193"),
        "performer_display": fields.String(example="dr. RINI SUSANTI, Sp.Rad"),

        "codind_code": fields.String(example="24648-8"),
        "coding_display": fields.String(example="XR Chest PA upright"),

        # Observation
        "performer_value": fields.String(example="Hasil Bacaan adalah ..."),

        # DiagnosticReport
        "conclusion_text": fields.String(example="Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru"),

        # DICOM processing
        "study": fields.String(required=True, example="1.2.840.113619.2.55.3.604688433.783.159975"),
        "patientid": fields.String(example="P10443013727"),
        "accesionnum": fields.String(example="20250002"),
    },
)



# -------------------------------
# Routes
# -------------------------------

@ns.route("/halo")
class Halo(Resource):
    def get(self):
        return {"message": "Halo dari Satu Sehat!"}, 200


@ns.route("/token")
class Token(Resource):
    def get(self):
        token, err = get_access_token()
        if err:
            return err, 502
        return {"access_token": token}, 200


@ns.route("/encounter")
@ns.expect(encounter_input, validate=False)
class EncounterCreate(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}

        # Build resource
        encounter = build_encounter_resource(data)

        # Auth
        token, err = get_access_token()
        if err:
            return err, 502

        # POST
        url = Config.SS_BASE_URL.rstrip("/") + "/Encounter"
        return post_fhir(url, token, encounter)


@ns.route("/service-req")
@ns.expect(servicereq_input, validate=False)
class ServiceRequestCreate(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}

        # Build resource
        sreq = build_servicereq_resource(data)

        # Auth
        token, err = get_access_token()
        if err:
            return err, 502

        # POST
        url = Config.SS_BASE_URL.rstrip("/") + "/ServiceRequest"
        return post_fhir(url, token, sreq)

@ns.route("/batch1")
@ns.expect(batch1_input, validate=False)
class Batch1(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}

        result, status = process_batch1(data)
        return result, status


@ns.route("/observation")
@ns.expect(observation_input, validate=False)
class ObservationCreate(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}

        # Build Observation resource
        try:
            obs = build_observation_resource(data)
        except Exception as e:
            return {"error": str(e)}, 400

        # Get token
        token, err = get_access_token()
        if err:
            return err, 502

        # POST to FHIR
        url = Config.SS_BASE_URL.rstrip("/") + "/Observation"
        return post_fhir(url, token, obs)

@ns.route("/conclusion")
@ns.expect(diagnostic_input, validate=False)
class DiagnosticCreate(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}

        # Build DiagnosticReport resource
        try:
            drep = build_diagnostic_resource(data)
        except Exception as e:
            return {"error": str(e)}, 400

        # Get token
        token, err = get_access_token()
        if err:
            return err, 502

        # POST to FHIR
        url = Config.SS_BASE_URL.rstrip("/") + "/DiagnosticReport"
        return post_fhir(url, token, drep)

@ns.route("/batch2")
@ns.expect(batch2_input, validate=False)
class Batch2(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        result, status = process_batch2(data)
        return result, status

@ns.route("/batch3")
@ns.expect(batch3_input, validate=False)
class Batch3(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        result, status = process_batch3(data)
        return result, status


@ns.route("/imageid/<string:acsn>")
class ImageId(Resource):
    def get(self, acsn):
        result, status = lookup_imaging_by_acsn(acsn)
        return result, status

@dicom_ns.route("/process")
class ProcessDicom(Resource):
    @dicom_ns.expect(dicom_model)
    def post(self):
        data = dicom_ns.payload
        result, status = process_dicom(data)
        return result, status

@ns.route("/batch4")
@ns.expect(batch4_input, validate=False)
class Batch4(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        result, status = process_batch4(data)
        return result, status
