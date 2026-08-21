from core.extensions import socketio
from flask import request
from flask_login import current_user
from extensions.live_messages.forms.start_live_chat import StartLiveChatForm
from extensions.live_messages.models import LiveChatClient
from core.extensions import db
from flask_socketio import emit, join_room

@socketio.on('start_chat')
def handle_start_chat(data):
    """
    Validate the incoming data using the StartLiveChatForm and emit a response back to the client.
    """

    form = StartLiveChatForm(data=data, meta={'csrf': False})

    if form.validate():
        new_client = LiveChatClient(
            fullname=form.fullname.data,
            email=form.email.data,
            phone_number=form.phone_number.data
        )
        db.session.add(new_client)
        db.session.commit()
        emit('start_chat', {'status': 'success', 'client_uuid': new_client.uuid})
        join_room(new_client.uuid)
    else:
        emit('start_chat', {'status': 'error', 'errors': form.errors})

@socketio.on('history')
def handle_history(data):
    room = data.get('client_uuid')
    if room:
        join_room(room)
        client = LiveChatClient.query.filter_by(uuid=room).first()
        emit('history', {'messages': []})

@socketio.on('send_message')
def handle_send_message(data):
    """
    Handle incoming messages from client or agent and broadcast them to the appropriate recipient.
    """
    if current_user.is_authenticated:
        # agent response
        pass
    else:
        client_uuid = data.get('client_uuid')
        content = data.get('content')
        content
        sender = 'client'
        if not client_uuid:
            emit('send_message', {'status': 'error', 'message': 'Client UUID is required.'})
            return
