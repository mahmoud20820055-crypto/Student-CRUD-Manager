"""Input validation for student payloads."""
import re
from datetime import date

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TEXT_FIELDS = ("student_code", "first_name", "last_name", "email", "major")
FIELDS = TEXT_FIELDS + ("gpa", "enrolled_year")


def validate_student(data: dict, partial: bool = False) -> tuple[dict, dict]:
    """Return (clean_data, errors). With partial=True only given fields are checked."""
    if not isinstance(data, dict):
        return {}, {"body": "JSON object expected"}

    clean, errors = {}, {}
    for field in FIELDS:
        if field not in data:
            if not partial:
                errors[field] = "is required"
            continue
        value = data[field]

        if field in TEXT_FIELDS:
            value = str(value).strip() if value is not None else ""
            if not value:
                errors[field] = "must not be empty"
            elif len(value) > 120:
                errors[field] = "must be at most 120 characters"
            elif field == "email" and not EMAIL_RE.match(value):
                errors[field] = "must be a valid email address"
            else:
                clean[field] = value.lower() if field == "email" else value
        elif field == "gpa":
            try:
                value = float(value)
            except (TypeError, ValueError):
                errors[field] = "must be a number"
                continue
            if not 0 <= value <= 4:
                errors[field] = "must be between 0.0 and 4.0"
            else:
                clean[field] = round(value, 2)
        elif field == "enrolled_year":
            try:
                value = int(value)
            except (TypeError, ValueError):
                errors[field] = "must be an integer"
                continue
            if not 1950 <= value <= date.today().year + 1:
                errors[field] = f"must be between 1950 and {date.today().year + 1}"
            else:
                clean[field] = value

    if partial and not clean and not errors:
        errors["body"] = "no updatable fields provided"
    return clean, errors
