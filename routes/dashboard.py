from .. import bp
from flask import render_template

@bp.route('/dashboard/live-messages/')
def messages():
    return render_template('dashboard/messages.html')