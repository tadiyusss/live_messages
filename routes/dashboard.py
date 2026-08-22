from flask_login import login_required
from core.utils.decorators import roles_required
from .. import bp
from flask import render_template
from ..models import LiveChatClient

    
@bp.route('/dashboard/live-messages/')
@login_required
@roles_required(['Administrator', 'Support Agent'])
def messages():
    clients = LiveChatClient.query.all()
    return render_template('dashboard/messages.html', clients=clients)