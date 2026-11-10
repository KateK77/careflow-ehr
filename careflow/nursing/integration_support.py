"""Synthetic, isolated fixtures shared only by the integration test modules."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone


# Keep the live workflow comfortably before local midnight without mocking clocks.
# This changes test settings only, never the application/production configuration.
TEST_CLINIC_ZONE = "UTC" if timezone.now().hour < 12 else "Etc/GMT+12"


class IntegrationFixture:
    def make_staff(self, password=None):
        self.staff = {}
        for role in ["Administrator", "FrontDesk", "Nurse", "Physician"]:
            actor = get_user_model().objects.create_user(username="integration-" + role.lower(), password=password)
            actor.groups.add(Group.objects.get_or_create(name=role)[0])
            self.staff[role] = actor

    def observation_time(self):
        return timezone.localtime(timezone.now() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M")

    def assessment_payload(self, version=0, **changes):
        return {"version": version, "chief_complaint": "Synthetic integration complaint", "observed_at": self.observation_time(),
                "encounter": "", "pain_score": 2, "observations": "Fictional nursing handoff", "ready_for_provider": True,
                "synthetic_confirmed": True, **changes}

    def vital_payload(self, version=0, **changes):
        return {"version": version, "observed_at": self.observation_time(), "encounter": "", "source": "measured",
                "systolic": 120, "diastolic": 80, "heart_rate": 70, "temperature": "37.2", "temperature_unit": "C",
                "source_detail": "Synthetic integration measurement", "synthetic_confirmed": True, **changes}

    def history_payload(self, label, **changes):
        return {"version": 0, "label": label, "comments": "Fictional integration history", "source": "documented",
                "source_detail": "Synthetic interview", "synthetic_confirmed": True, **changes}

    def soap_payload(self, version=0, **changes):
        return {"version": version, "subjective": "Fictional complaint", "objective": "Synthetic nursing information reviewed",
                "assessment": "Fictional assessment only", "plan": "Fictional plan only", "synthetic_confirmed": True, **changes}
