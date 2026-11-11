from django import template

register = template.Library()
EVENTS = {
    "pharmacy_claim": "Pharmacy order claimed",
    "pharmacy_approve": "Verification approved",
    "pharmacy_clarify": "Clarification requested",
    "pharmacy_respond": "Physician clarification response",
    "pharmacy_reject": "Verification rejected",
    "pharmacy_dispense": "Simulated dispensing recorded",
    "pharmacy_view": "Pharmacy requisition viewed",
    "med_catalog_create": "Medication catalog revision created",
    "med_catalog_activate": "Medication catalog revision activated",
    "med_catalog_retire": "Medication catalog revision retired",
    "med_order_create": "Medication draft created",
    "med_order_edit": "Medication draft edited",
    "med_order_sign": "Medication order signed",
    "med_order_cancel": "Medication order cancelled",
    "lab_catalog_create": "Catalog revision created", "lab_catalog_activate": "Catalog revision activated",
    "lab_catalog_deactivate": "Catalog revision deactivated", "lab_order_create": "Laboratory draft created",
    "lab_order_edit": "Laboratory draft edited", "lab_order_submit": "Laboratory order submitted",
    "lab_order_cancel": "Laboratory order cancelled",
    "lab_assign": "Lab staff assigned",
    "lab_claim": "Lab order claimed",
    "lab_collect": "Specimen collected",
    "lab_correct_collection": "Specimen collection corrected",
    "lab_reject": "Specimen rejected",
    "lab_receive": "Specimen received",
    "lab_recollect": "Recollection requested",
    "lab_result_create": "Result draft created",
    "lab_result_save": "Result draft saved",
    "lab_abandon": "Result draft abandoned",
    "lab_publish": "Laboratory report published",
    "lab_processing_view": "Laboratory processing viewed",
    "lab_worklist_view": "Laboratory worklist viewed",
    "lab_acknowledge": "Laboratory publication acknowledged",
    "lab_correct": "Correction draft created",
    "lab_reassign": "Review responsibility reassigned",
    "lab_withdraw": "Laboratory report withdrawn",
    "lab_report_view": "Laboratory report viewed",
    "lab_review_assignment_backfill": "Initial review responsibility recorded",
    "patient_create": "Patient registered", "patient_update": "Demographics updated", "patient_view": "Demographics viewed",
    "appointment_create": "Appointment booked", "appointment_reschedule": "Appointment rescheduled",
    "appointment_arrive": "Patient checked in", "appointment_cancel": "Appointment cancelled", "appointment_no_show": "No-show recorded",
    "encounter_start": "Encounter started", "encounter_complete": "Encounter completed",
    "note_create": "SOAP draft created", "note_edit": "SOAP draft updated", "note_sign": "SOAP note signed",
    "history_allergy_state_sync": "Allergy assessment updated", "history_allergy_state_review": "Allergy assessment reviewed",
}
DOMAINS = {"medical": "Medical history", "problems": "Problem", "allergies": "Allergy", "medications": "Medication statement", "diagnoses": "Encounter diagnosis"}
FIELDS = {"mrn": "MRN", "dob": "Date of birth", "signed_at": "Signing time", "checked_in_by": "Check-in staff",
          "checked_in_at": "Check-in time", "observed_at": "Observation time", "recorded_by": "Recording nurse",
          "updated_by": "Last editor", "reviewed_by": "Reviewing staff", "ready_for_provider": "Ready for provider",
          "pk": "Record number", "id": "Record number"}


@register.filter
def event_label(value):
    value = str(value)
    if value in EVENTS:
        return EVENTS[value]
    for kind, label in DOMAINS.items():
        for suffix, action in {"create": "recorded", "edit": "updated", "review": "review recorded"}.items():
            if value == f"history_{kind}_{suffix}":
                return f"{label} {action}"
    for kind, label in {"assessment": "Rooming assessment", "vitals": "Vital observation"}.items():
        for suffix, action in {"create": "recorded", "edit": "corrected"}.items():
            if value == f"nursing_{kind}_{suffix}":
                return f"{label} {action}"
    return value.replace("_", " ").capitalize() if "_" in value else value


@register.filter
def field_label(value):
    return FIELDS.get(str(value), str(value).replace("_", " ").capitalize())


@register.filter
def field_labels(values):
    return [field_label(value) for value in values]
