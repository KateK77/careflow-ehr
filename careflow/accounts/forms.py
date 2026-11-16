from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password
from django.core.validators import RegexValidator
from .models import Enrollment, STAFF_ROLES

username_validator = RegexValidator(r"\A[a-z0-9_.-]{3,40}\Z",
    "Use 3–40 lowercase letters, digits, dots, hyphens or underscores.")


class SignupForm(forms.Form):
    username = forms.CharField(min_length=3, max_length=40, validators=[username_validator],
        widget=forms.TextInput(attrs={"autocomplete": "username", "autocapitalize": "none", "spellcheck": "false"}),
        help_text="Use 3–40 lowercase letters, digits, dots, hyphens or underscores. No email required.")
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Use at least 12 characters. Avoid common or entirely numeric passwords.")
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    requested_role = forms.ChoiceField(choices=[(r, r) for r in STAFF_ROLES], label="Requested staff role")
    synthetic_only = forms.BooleanField(label="I will use only fictional patient information in this demonstration.")

    def __init__(self, *args, kind, **kwargs):
        super().__init__(*args, label_suffix="", **kwargs)
        if kind == "patient":
            del self.fields["requested_role"]

    def clean_username(self):
        value = self.cleaned_data["username"]
        if get_user_model().objects.filter(username__iexact=value).exists():
            raise forms.ValidationError("This username is unavailable. Choose another.")
        return value

    def clean(self):
        data = super().clean()
        if data.get("password1") and data.get("password2"):
            if data["password1"] != data["password2"]:
                self.add_error("password2", "The passwords do not match.")
            else:
                try:
                    validate_password(data["password1"], get_user_model()(username=data.get("username", "")))
                except forms.ValidationError as error:
                    self.add_error("password1", error)
        return data


class ReviewForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, label_suffix="", **kwargs)

    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    decision = forms.ChoiceField(choices=[("approve", "Approve"), ("reject", "Reject")])
    role = forms.ChoiceField(choices=[("", "No role for rejection")] + [(r, r) for r in STAFF_ROLES], required=False)
    reason = forms.CharField(max_length=500, widget=forms.Textarea(attrs={"rows": 3}))

    def clean(self):
        data = super().clean()
        if data.get("decision") == "approve" and not data.get("role"):
            self.add_error("role", "Choose an approved staff role.")
        return data


class StaffAuthenticationForm(AuthenticationForm):
    def get_invalid_login_error(self):
        # Explain a pending application only after proving its password. Never
        # authenticate inactive accounts or expose their review status by username alone.
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if username and password:
            item = Enrollment.objects.select_related("user").filter(
                user__username=username, user__is_active=False,
                kind="staff", status="pending").first()
            if item is not None:
                valid_password = check_password(password, item.user.password)
                if valid_password:
                    return forms.ValidationError(
                        "Your staff application is awaiting Administrator approval. "
                        "Ask the local operator to review it in Staff applications, "
                        "then sign in with the same username and password.",
                        code="staff_pending",
                    )
            else:
                # Keep an extra password-hash operation for other failed logins too.
                get_user_model()().set_password(password)
        return super().get_invalid_login_error()
