from flask_wtf import FlaskForm
from wtforms import FileField
from wtforms.validators import DataRequired
from .validations import validate_file_size

class SendFileForm(FlaskForm):
    file = FileField('File', validators=[DataRequired(), validate_file_size])
