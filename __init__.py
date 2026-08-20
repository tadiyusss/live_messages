from flask import Blueprint
from .metadata import TEMPLATE_FOLDER, STATIC_FOLDER
from .initialization.sidebar import initialize_sidebar

bp = Blueprint('live_messages', __name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER, static_url_path="/static/live_messages")

from .routes import dashboard

def init_extension(app, db):
    with app.app_context():

        db.create_all()
        initialize_sidebar()
    return bp 