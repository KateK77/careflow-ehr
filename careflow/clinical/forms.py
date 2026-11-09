from django import forms

from .services import SECTIONS


class NoteForm(forms.Form):
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    subjective = forms.CharField(required=False, max_length=20000, widget=forms.Textarea(attrs={"rows": 5}))
    objective = forms.CharField(required=False, max_length=20000, widget=forms.Textarea(attrs={"rows": 5}))
    assessment = forms.CharField(required=False, max_length=20000, widget=forms.Textarea(attrs={"rows": 5}))
    plan = forms.CharField(required=False, max_length=20000, widget=forms.Textarea(attrs={"rows": 5}))
    synthetic_confirmed = forms.BooleanField(label="I confirm this note contains synthetic information only.")

    @classmethod
    def for_note(cls, note):
        initial = {key: getattr(note, key) for key in SECTIONS} if note else {}
        return cls(initial={**initial, "version": note.version if note else 0})


class VersionForm(forms.Form):
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)


class SignForm(VersionForm):
    confirmed = forms.BooleanField(label="I have reviewed all four sections and confirm signing this synthetic note. Signing locks its content.")
