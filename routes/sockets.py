from core.extensions import socketio
from flask import request
from flask_login import current_user
from extensions.live_messages.forms.start_live_chat import StartLiveChatForm
from extensions.live_messages.models import LiveChatClient, Messages
from core.extensions import db
from flask_mail import Message
from core.extensions import mail
from flask_socketio import emit, join_room, leave_room
from extensions.live_messages.utils.messages import is_client_uuid_valid, get_all_clients, mark_client_messages_read, get_message_history, serialize_client, serialize_message, get_all_unaccommodated_clients
from core.models.users import User, Role, UserRole

ADMIN_ROOM = 'Administrators'
ALLOWED_ROLES = ['Administrator', 'Support Agent']
_connected_users = dict()

@socketio.on('connect')
def handle_connect():

    if not current_user.is_authenticated:
        _connected_users[request.sid] = {
            "type": "client",
            "current_room": None
        }
        return

    if not any(role.role.name in ALLOWED_ROLES for role in current_user.user_roles):
        _connected_users[request.sid] = {
            "type": "client",
            "current_room": None
        }
        return

    _connected_users[request.sid] = {
        "type": "admin",
        "current_room": None
    }
    join_room(ADMIN_ROOM)
    unaccommodated_clients = [serialize_client(client) for client in get_all_unaccommodated_clients()]
    emit('unaccommodated-clients', {'success': True, 'clients': unaccommodated_clients})
@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in _connected_users:
        user_info = _connected_users.pop(request.sid)
        print(f"{user_info['type'].capitalize()} Disconnected: {request.sid}")


@socketio.on('new-client')
def handle_new_client(data):
    form = StartLiveChatForm(data=data, meta={'csrf': False})

    if not form.validate():
        emit('new-client', {'success': False, 'error': 'Invalid form data.', 'errors': form.errors})
        return

    new_client = LiveChatClient(
        fullname=form.fullname.data,
        email=form.email.data,
        phone_number=form.phone_number.data
    )
    db.session.add(new_client)
    db.session.commit()

    _connected_users[request.sid] = {
        "type": "client",
        "current_room": new_client.uuid
    }
    emit('new-client', {'success': True, 'client': serialize_client(new_client)}, room=request.sid)
    emit('new-client', {'success': True, 'client': serialize_client(new_client)}, room=ADMIN_ROOM)


@socketio.on('validate-client-uuid')
def handle_validate_client_uuid(data):
    client_uuid = data.get('client_uuid')

    if not client_uuid:
        emit('validate-client-uuid', {'success': False, 'error': 'Client UUID is required.'}, room=request.sid)
        return

    is_valid = is_client_uuid_valid(client_uuid)

    if not is_valid:
        emit('validate-client-uuid', {'success': False}, room=request.sid)
        return

    _connected_users[request.sid] = {
        "type": "client",
        "current_room": client_uuid
    }
    
    history = get_message_history(client_uuid)
    emit('validate-client-uuid', {'success': True}, room=request.sid)
    emit('get-history', {'success': True, 'messages': history}, room=request.sid)

@socketio.on('send-message')
def handle_send_message(data):
    pass