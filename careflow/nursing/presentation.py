from .access import appointments_for
from .models import RoomingAssessment, VitalObservation


FIXED_UNITS = {"systolic": "mmHg", "diastolic": "mmHg", "heart_rate": "beats/min",
               "respiratory_rate": "breaths/min", "oxygen_saturation": "%", "pain_score": "/10"}
LABELS = {"systolic": "Systolic BP", "diastolic": "Diastolic BP", "heart_rate": "Heart rate",
          "respiratory_rate": "Respiratory rate", "temperature": "Temperature", "oxygen_saturation": "Oxygen saturation",
          "height": "Height", "weight": "Weight", "pain_score": "Pain score"}


def value_with_unit(record, name):
    value = getattr(record, name)
    if value is None:
        return "Not recorded"
    unit = FIXED_UNITS.get(name)
    if unit is None:
        unit = getattr(record, "get_" + name + "_unit_display")()
    return f"{value} {unit}"


def values(record):
    return [(label, value_with_unit(record, name)) for name, label in LABELS.items()]


def chart_context(user, patient, appointment_id=None):
    appointments = appointments_for(user).filter(patient=patient)
    if appointment_id:
        appointments = appointments.filter(pk=appointment_id)
    assessments = RoomingAssessment.objects.filter(appointment__in=appointments).select_related("recorded_by", "appointment")
    vitals = VitalObservation.objects.filter(appointment__in=appointments).select_related("recorded_by", "appointment")
    latest = vitals.first()
    return {"latest_nursing_assessment": assessments.first(), "latest_vitals": latest,
            "latest_vital_values": values(latest) if latest else [], "nursing_appointments": appointments.order_by("-start_at")[:10]}
