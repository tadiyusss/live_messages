from wtforms.validators import ValidationError

def validate_phone_number(form, field):
    phone_number = field.data
    if not phone_number.isdigit():
        raise ValidationError('Phone number must contain only digits.')
    if len(phone_number) < 10 or len(phone_number) > 11:
        raise ValidationError('Phone number must be between 10 and 11 digits long.')