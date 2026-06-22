from django.core.exceptions import ValidationError

def validate_reflection(value):
    if value:
        words = len(value.split())
        if words > 100:
            raise ValidationError("Maksimalno 100 riječi.")