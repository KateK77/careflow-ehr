from django import forms

DATE_ERROR = "Enter a valid date in YYYY-MM-DD format with a four-digit year (0001–9999)."


def configure_date_field(field, maximum="9999-12-31", minimum="0001-01-01"):
    """Use ISO input without arbitrarily excluding legitimate historical years."""
    field.input_formats = ["%Y-%m-%d"]
    field.error_messages["invalid"] = DATE_ERROR
    field.widget = forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "min": minimum, "max": maximum})
    return field
