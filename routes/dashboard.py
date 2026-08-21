from .. import bp
from flask import render_template
from ..models import LiveChatClient

@bp.route('/dashboard/live-messages/')
def messages():
    clients = LiveChatClient.query.all()
    return render_template('dashboard/messages.html', clients=clients)