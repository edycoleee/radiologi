// =========================
// ALERT SYSTEM
// =========================
function showAlert(message, type = "info") {
    const box = document.getElementById('alertBox');
    box.className = `alert alert-${type}`;
    box.textContent = message;
    box.classList.remove('d-none');

    // Auto hide setelah 4 detik
    setTimeout(() => {
        box.classList.add('d-none');
    }, 4000);
}


// =========================
// LOADING BADGE
// =========================
function showLoading() {
    const badge = document.getElementById('loadingBadge');
    badge.classList.remove('d-none');
}

function hideLoading() {
    const badge = document.getElementById('loadingBadge');
    badge.classList.add('d-none');
}


// =========================
// GENERIC POST JSON (AMAN)
// =========================
async function postJson(url, body, resultId) {
    showLoading();
    showAlert("Memproses permintaan...", "warning");

    try {
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const text = await resp.text();
        let data;

        try {
            data = JSON.parse(text);
        } catch {
            data = { raw: text };
        }

        showResult(resultId, data, resp.status);

        if (!resp.ok) {
            showAlert(`Error: ${data.message || "Terjadi kesalahan"}`, "danger");
        } else {
            showAlert("Permintaan berhasil diproses", "success");
        }

    } catch (err) {
        showAlert(`Network Error: ${err.message}`, "danger");
        showResult(resultId, { error: err.message }, 'ERR');

    } finally {
        hideLoading();   // SELALU jalan
    }
}




// Helper: show JSON result in a box
function showResult(id, data, status) {
    const box = document.getElementById(id);
    if (!box) return;
    box.style.display = 'block';
    box.textContent = `HTTP ${status}\n` + JSON.stringify(data, null, 2);
}

// // Helper: generic POST JSON
// async function postJson(url, body, resultId) {
//     try {
//         const resp = await fetch(url, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify(body)
//         });
//         const text = await resp.text();
//         let data;
//         try { data = JSON.parse(text); } catch { data = { raw: text }; }
//         showResult(resultId, data, resp.status);
//     } catch (err) {
//         showResult(resultId, { error: err.message }, 'ERR');
//     }
// }

// // Helper: GET JSON
// async function getJson(url, resultId) {
//     try {
//         const resp = await fetch(url);
//         const text = await resp.text();
//         let data;
//         try { data = JSON.parse(text); } catch { data = { raw: text }; }
//         showResult(resultId, data, resp.status);
//     } catch (err) {
//         showResult(resultId, { error: err.message }, 'ERR');
//     }
// }

// Helper: serialize form to object
function formToJson(form) {
    const obj = {};
    const fd = new FormData(form);
    for (const [k, v] of fd.entries()) {
        if (v !== '') obj[k] = v;
    }
    return obj;
}

// Auto-fill payloads
function setupAutofill() {
    document.querySelectorAll('[data-autofill]').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.getAttribute('data-autofill');
            const form = btn.closest('form');
            if (!form) return;

            const set = (name, value) => {
                const el = form.querySelector(`[name="${name}"]`);
                if (el) el.value = value;
            };

            const now = new Date().toISOString();

            switch (type) {
                case 'dicom-process':
                    set('study', '1.2.840.113619.2.55.3.604688433.783.159975');
                    set('patientid', 'P10443013727');
                    set('accesionnum', '20250002');
                    break;

                case 'encounter':
                    set('identifier_value', 'RG2023I0000175');

                    // Subject
                    set('subject_id', 'P10443013727');
                    set('subject_reference', 'Patient/P10443013727');
                    set('subject_display', 'MILA YASYFI TASBIHA');

                    // Practitioner
                    set('individual_id', '10016869420');
                    set('individual_reference', 'Practitioner/10016869420');
                    set('individual_display', 'dr. ARIAWAN SETIADI, Sp.A');

                    // Period
                    set('period_start', now);
                    set('period_end', new Date(Date.now() + 10 * 60000).toISOString()); // +10 minutes

                    // Location
                    set('location_id', 'ecff1c64-3f62-4469-b577-ea38f263b276');
                    set('location_reference', 'Location/ecff1c64-3f62-4469-b577-ea38f263b276');
                    set('location_display', 'Ruang 1, Poliklinik Anak, Lantai 1, Gedung Poliklinik');
                    break;


                case 'servicereq':
                    set('identifier_value', 'RG2023I0000176');
                    set('noacsn', '20250002');
                    set('subject_id', 'P10443013727');
                    set('encounter_id', '015aa41f-88d7-4b0b-b5f1-d511522bfa87');
                    set('period_start', now);

                    // Tambahan baru
                    set('requester_reference', 'Practitioner/10016869420');
                    set('requester_display', 'dr. ARIAWAN SETIADI, Sp.A');
                    set('performer_reference', 'Practitioner/10000504193');
                    set('performer_display', 'dr. RINI SUSANTI, Sp.Rad');
                    break;


                case 'observation':
                    set('identifier_value', 'RG2023I0000174');

                    set('codind_code', '24648-8');
                    set('coding_display', 'XR Chest PA upright');

                    set('subject_id', 'P10443013727');
                    set('subject_display', 'MILA YASYFI TASBIHA');

                    set('encounter_id', '6dc2dc13-0b5a-4105-996e-6403e43be60a');
                    set('period_start', now);

                    set('performer_id', '10000504193');
                    set('performer_display', 'dr. RINI SUSANTI, Sp.Rad');
                    set('performer_value', 'Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru');

                    set('service_request_id', 'a33163ec-ba77-4775-8d20-83035b76e668');
                    set('imaging_study_id', '75b7e9d0-c079-419c-84f8-8dba7b9cd585');
                    break;

                case 'diagnostic':
                    set('identifier_value', 'RG2023I0000174');

                    set('codind_code', '24648-8');
                    set('coding_display', 'XR Chest PA upright');

                    set('subject_id', 'P10443013727');
                    set('encounter_id', '6dc2dc13-0b5a-4105-996e-6403e43be60a');
                    set('period_start', now);

                    set('performer_id', '10000504193');

                    set('imaging_study_id', '75b7e9d0-c079-419c-84f8-8dba7b9cd585');
                    set('observation_id', '82b9af58-c98d-4263-9a6f-9a04fdfec43a');
                    set('service_request_id', 'a33163ec-ba77-4775-8d20-83035b76e668');

                    set('conclusion_text', 'Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru');
                    break;

                case 'batch1':
                    set('identifier_value', 'RG2023I0000175');

                    // Encounter
                    set('subject_id', 'P10443013727');
                    set('subject_reference', 'Patient/P10443013727');
                    set('subject_display', 'MILA YASYFI TASBIHA');

                    set('individual_id', '10016869420');
                    set('individual_reference', 'Practitioner/10016869420');
                    set('individual_display', 'dr. ARIAWAN SETIADI, Sp.A');

                    set('period_start', '2025-08-01T05:57:41+00:00');
                    set('period_end', '2025-08-01T06:07:41+00:00');

                    set('location_id', 'ecff1c64-3f62-4469-b577-ea38f263b276');
                    set('location_reference', 'Location/ecff1c64-3f62-4469-b577-ea38f263b276');
                    set('location_display', 'Ruang 1, Poliklinik Anak');

                    // ServiceRequest
                    set('noacsn', '20250002');
                    set('requester_reference', 'Practitioner/10016869420');
                    set('requester_display', 'dr. ARIAWAN SETIADI, Sp.A');
                    set('performer_reference', 'Practitioner/10000504193');
                    set('performer_display', 'dr. RINI SUSANTI, Sp.Rad');
                    break;


                case 'batch2':
                    set('identifier_value', 'RG2023I0000174');

                    set('codind_code', '24648-8');
                    set('coding_display', 'XR Chest PA upright');

                    set('subject_id', 'P10443013727');
                    set('subject_display', 'MILA YASYFI TASBIHA');

                    set('encounter_id', '6dc2dc13-0b5a-4105-996e-6403e43be60a');
                    set('period_start', now);

                    set('performer_id', '10000504193');
                    set('performer_display', 'dr. RINI SUSANTI, Sp.Rad');
                    set('performer_value', 'Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru');

                    set('service_request_id', 'a33163ec-ba77-4775-8d20-83035b76e668');
                    set('imaging_study_id', '75b7e9d0-c079-419c-84f8-8dba7b9cd585');

                    set('conclusion_text', 'Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru');
                    break;

                case 'batch3':
                    set('identifier_value', 'RG2023I0000175');

                    // Encounter
                    set('subject_id', 'P10443013727');
                    set('subject_reference', 'Patient/P10443013727');
                    set('subject_display', 'MILA YASYFI TASBIHA');

                    set('individual_id', '10016869420');
                    set('individual_reference', 'Practitioner/10016869420');
                    set('individual_display', 'dr. ARIAWAN SETIADI, Sp.A');

                    set('period_start', '2025-08-01T05:57:41+00:00');
                    set('period_end', '2025-08-01T06:07:41+00:00');

                    set('location_id', 'ecff1c64-3f62-4469-b577-ea38f263b276');
                    set('location_reference', 'Location/ecff1c64-3f62-4469-b577-ea38f263b276');
                    set('location_display', 'Ruang 1, Poliklinik Anak');

                    // ServiceRequest
                    set('noacsn', '20250002');
                    set('requester_reference', 'Practitioner/10016869420');
                    set('requester_display', 'dr. ARIAWAN SETIADI, Sp.A');

                    set('performer_id', '10000504193');
                    set('performer_reference', 'Practitioner/10000504193');
                    set('performer_display', 'dr. RINI SUSANTI, Sp.Rad');

                    // Observation
                    set('codind_code', '24648-8');
                    set('coding_display', 'XR Chest PA upright');
                    set('performer_value', 'Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru');

                    // ImagingStudy
                    set('imaging_study_id', '75b7e9d0-c079-419c-84f8-8dba7b9cd585');

                    // DiagnosticReport
                    set('conclusion_text', 'Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru');
                    break;


                case 'batch4':
                    set('identifier_value', 'RG2023I0000175');

                    // Encounter
                    set('subject_id', 'P10443013727');
                    set('subject_reference', 'Patient/P10443013727');
                    set('subject_display', 'MILA YASYFI TASBIHA');

                    set('individual_id', '10016869420');
                    set('individual_reference', 'Practitioner/10016869420');
                    set('individual_display', 'dr. ARIAWAN SETIADI, Sp.A');

                    set('period_start', '2025-08-01T05:57:41+00:00');
                    set('period_end', '2025-08-01T06:07:41+00:00');

                    set('location_id', 'ecff1c64-3f62-4469-b577-ea38f263b276');
                    set('location_reference', 'Location/ecff1c64-3f62-4469-b577-ea38f263b276');
                    set('location_display', 'Ruang 1, Poliklinik Anak');

                    // ServiceRequest
                    set('noacsn', '20250002');
                    set('requester_reference', 'Practitioner/10016869420');
                    set('requester_display', 'dr. ARIAWAN SETIADI, Sp.A');

                    set('performer_id', '10000504193');
                    set('performer_reference', 'Practitioner/10000504193');
                    set('performer_display', 'dr. RINI SUSANTI, Sp.Rad');

                    set('codind_code', '24648-8');
                    set('coding_display', 'XR Chest PA upright');

                    // Observation
                    set('performer_value', 'Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru');

                    // DiagnosticReport
                    set('conclusion_text', 'Hasil Bacaan adalah Tak tampak bercak pada kedua lapangan paru');

                    // DICOM
                    set('study', '1.2.840.113619.2.55.3.604688433.783.159975');
                    set('patientid', 'P10443013727');
                    set('accesionnum', '20250002');
                    break;


                case 'imaging':
                    set('acsn', '20250002');
                    break;
            }
        });
    });
}

// Form bindings
function setupForms() {
    // DICOM process
    document.getElementById('form-dicom-process').addEventListener('submit', e => {
        e.preventDefault();
        const body = formToJson(e.target);
        postJson('/api/dicom/process', body, 'result-dicom-process');
    });

    // Encounter
    document.getElementById('form-encounter').addEventListener('submit', e => {
        e.preventDefault();
        const body = formToJson(e.target);
        postJson('/api/satset/encounter', body, 'result-encounter');
    });

    // ServiceRequest
    document.getElementById('form-servicereq').addEventListener('submit', e => {
        e.preventDefault();
        const body = formToJson(e.target);
        postJson('/api/satset/service-req', body, 'result-servicereq');
    });

    // Observation
    document.getElementById('form-observation').addEventListener('submit', e => {
        e.preventDefault();
        const body = formToJson(e.target);
        postJson('/api/satset/observation', body, 'result-observation');
    });

    // DiagnosticReport
    document.getElementById('form-diagnostic').addEventListener('submit', e => {
        e.preventDefault();
        const body = formToJson(e.target);
        postJson('/api/satset/conclusion', body, 'result-diagnostic');
    });

    // Batch1
    document.getElementById('form-batch1').addEventListener('submit', e => {
        e.preventDefault();
        const body = formToJson(e.target);
        postJson('/api/satset/batch1', body, 'result-batch1');
    });

    // Batch2
    document.getElementById('form-batch2').addEventListener('submit', e => {
        e.preventDefault();
        const body = formToJson(e.target);
        postJson('/api/satset/batch2', body, 'result-batch2');
    });

    // Batch3
    document.getElementById('form-batch3').addEventListener('submit', e => {
        e.preventDefault();
        const body = formToJson(e.target);
        postJson('/api/satset/batch3', body, 'result-batch3');
    });

    // Batch4
    document.getElementById('form-batch4').addEventListener('submit', e => {
        e.preventDefault();
        const body = formToJson(e.target);
        postJson('/api/satset/batch4', body, 'result-batch4');
    });

    // Imaging lookup
    document.getElementById('form-imaging-lookup').addEventListener('submit', e => {
        e.preventDefault();
        const body = formToJson(e.target);
        const acsn = body.acsn;
        if (!acsn) {
            showResult('result-imaging-lookup', { error: 'ACSN required' }, 'ERR');
            return;
        }
        getJson(`/api/satset/imageid/${encodeURIComponent(acsn)}`, 'result-imaging-lookup');
    });
}

document.addEventListener('DOMContentLoaded', () => {
    setupAutofill();
    setupForms();
});
