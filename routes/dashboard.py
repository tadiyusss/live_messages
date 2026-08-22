from flask_login import login_required
from core.utils.decorators import roles_required
from .. import bp
from flask import render_template, redirect, url_for
from ..models import LiveChatClient
from core.extensions import db
    
@bp.route('/dashboard/live-messages/')
@login_required
@roles_required(['Administrator', 'Support Agent'])
def messages():
    clients = LiveChatClient.query.all()
    return render_template('dashboard/messages.html', clients=clients)

@bp.route('/dashboard/live-messages/delete/<string:client_uuid>')
@login_required
@roles_required(['Administrator', 'Support Agent'])
def delete_conversation(client_uuid):
    client = LiveChatClient.query.filter_by(uuid=client_uuid).first_or_404()
    messages = client.messages
    for message in messages:
        message.delete()
    db.session.delete(client)
    db.session.commit()
    return redirect(url_for('live_messages.messages'))
    