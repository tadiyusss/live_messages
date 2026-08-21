
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField
from wtforms.validators import DataRequired, Email, Length
from .validations import validate_phone_number

INPUT_CLASS = "w-full border border-emerald-200 bg-gray-50 focus:outline-none focus:ring-1 focus:ring-emerald-800/20 rounded px-4 py-2 text-sm"

class StartLiveChatForm(FlaskForm):
    fullname = StringField('Full Name', validators=[DataRequired()], render_kw={"class": INPUT_CLASS, "placeholder": "Enter your name here...", "x-model":"start_chat_form_data.fullname"})
    email = EmailField('Email', validators=[DataRequired(), Email()], render_kw={"class": INPUT_CLASS, "placeholder": "Enter your email here...", "x-model":"start_chat_form_data.email"})
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=11), validate_phone_number], render_kw={"class": INPUT_CLASS, "placeholder": "Enter your phone number here...", "x-model":"start_chat_form_data.phone_number"})