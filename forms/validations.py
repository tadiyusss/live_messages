from wtforms.validators import ValidationError

MAX_FILE_SIZE = 100 * 1024 * 1024

def validate_file_size(form, field):
    if not field.data:
        return
    field.data.stream.seek(0, 2)
    file_size = field.data.stream.tell()
    field.data.stream.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise ValidationError('File size must be less than 100MB.')

def validate_phone_number(form, field):
    phone_number = field.data
    if not phone_number.isdigit():
        raise ValidationError('Phone number must contain only digits.')
    if len(phone_number) < 10 or len(phone_number) > 11:
        raise ValidationError('Phone number must be between 10 and 11 digits long.')