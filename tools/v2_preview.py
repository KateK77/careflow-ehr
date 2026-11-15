"""Start an isolated local v2 preview. Never open an existing database."""
import argparse
import getpass
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def allocate_database(parent):
    parent.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="v2-preview-", dir=parent))
    return folder / "preview.sqlite3"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8012)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use a local port between 1024 and 65535.")
    if "django.conf" in sys.modules:
        raise RuntimeError("Run this launcher in a fresh Python process.")
    password = os.environ.pop("CAREFLOW_V2_PASSWORD", "") or getpass.getpass(
        "Choose a synthetic demo password (12+ characters; input hidden): ")
    database = allocate_database(ROOT / ".venv" / "uat-followup")
    os.environ["CAREFLOW_DB_PATH"] = str(database)
    os.environ["DJANGO_SETTINGS_MODULE"] = "careflow.settings"
    os.environ["CAREFLOW_ALLOW_DEMO_SEED"] = "1"
    os.environ["CAREFLOW_DEMO_PASSWORD"] = password
    sys.path.insert(0, str(ROOT))

    import django
    django.setup()
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from django.contrib.auth.password_validation import validate_password
    from django.core.management import call_command
    from django.utils import timezone
    from datetime import timedelta
    from careflow.patients.models import Patient
    from careflow.portal.models import PatientPortalAccount
    from careflow.scheduling.services import save_appointment

    if Path(settings.DATABASES["default"]["NAME"]).resolve() != database.resolve() or database.exists():
        raise RuntimeError("Preview refused: database must be new and isolated.")
    validate_password(password)
    call_command("migrate", interactive=False, verbosity=0)
    call_command("seed_synthetic", verbosity=0)
    user_model = get_user_model()
    for role, username in (
        ("Lab Staff", "lab.demo"), ("Pharmacist", "pharmacist.demo"),
        ("BillingStaff", "billing.demo"), ("RadiologyStaff", "radiology.demo"),
        ("HospitalOperations", "hospital.demo"),
    ):
        user = user_model.objects.create_user(username, password=password,
            first_name="Synthetic", last_name=role, email=username + "@example.invalid")
        user.groups.add(Group.objects.get_or_create(name=role)[0])
    for index in (1, 2):
        user = user_model.objects.create_user(f"patient{index}.demo", password=password,
            first_name="Synthetic", last_name=f"Patient {index}")
        PatientPortalAccount.objects.create(
            user=user, patient=Patient.objects.get(mrn=f"DEMO-{index:04d}"))
    physician = user_model.objects.get(username="physician.demo")
    actor = user_model.objects.get(username="frontdesk.demo")
    for index in range(1, 4):
        save_appointment(actor, {
            "patient": Patient.objects.get(mrn=f"DEMO-{index:04d}"),
            "physician": physician,
            "start_at": timezone.now().replace(second=0, microsecond=0) + timedelta(hours=index),
            "duration": 30, "appointment_type": "Synthetic preview",
            "reason": "Fictional local demonstration only.",
        })
    os.environ.pop("CAREFLOW_DEMO_PASSWORD", None)
    del password
    print(f"New synthetic preview database: {database}")
    print("Staff: administrator.demo, frontdesk.demo, physician.demo, nurse.demo,")
    print("       lab.demo, pharmacist.demo, billing.demo, radiology.demo, hospital.demo")
    print("Patients: patient1.demo and patient2.demo (separate linked records).")
    print("Use the password you supplied. No existing database was opened.")
    print(f"Preview: http://127.0.0.1:{args.port}/")
    if not args.prepare_only:
        call_command("runserver", f"127.0.0.1:{args.port}", use_reloader=False)


if __name__ == "__main__":
    main()
