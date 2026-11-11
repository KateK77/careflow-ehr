from django.contrib.auth.views import LoginView, LogoutView

from careflow.patients.models import AuditEvent


class DemoLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        from careflow.labs.access import is_lab
        from careflow.patients.access import roles_for
        from django.urls import reverse
        from careflow.medications.pharmacy_access import is_pharmacist
        if is_pharmacist(self.request.user) and not roles_for(self.request.user):
            return reverse("pharmacy_worklist")
        if is_lab(self.request.user) and not roles_for(self.request.user):
            return reverse("lab_worklist")
        return super().get_success_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditEvent.objects.create(actor=self.request.user, action="login")
        return response

    def form_invalid(self, form):
        AuditEvent.objects.create(action="login_failed", outcome="denied")
        return super().form_invalid(form)


class DemoLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        actor = request.user if request.user.is_authenticated else None
        response = super().post(request, *args, **kwargs)
        AuditEvent.objects.create(actor=actor, action="logout")
        return response
