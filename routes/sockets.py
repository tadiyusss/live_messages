from core.extensions import socketio
from flask import request
from flask_login import current_user
from extensions.live_messages.forms.start_live_chat import StartLiveChatForm
from extensions.live_messages.models import LiveChatClient, Messages
from core.extensions import db
from flask_socketio import emit, join_room, leave_room
from extensions.live_messages.utils.messages import (
    is_client_assigned,
    is_client_uuid_valid,
    mark_client_messages_read,
    get_message_history,
    serialize_client,
    serialize_message,
    get_all_unassigned_clients,
    get_all_clients_assigned_to_agent,
    is_client_online,
    send_message_notification,
    send_new_client_notification_to_al_agents
)

ADMIN_ROOM = 'Administrators'
ALLOWED_ROLES = ['Administrator', 'Support Agent']
_connected_users = dict()


def _get_user():
    return _connected_users.get(request.sid)


def _is_admin(user):
    return bool(user) and user.get('type') == 'admin'


def _owns_client(user, client_uuid):
    return (
        bool(user)
        and user.get('type') == 'client'
        and user.get('current_room') == client_uuid
    )


def _can_access_client(user, client_uuid):
    return _is_admin(user) or _owns_client(user, client_uuid)


def _deny(event, error='Unauthorized.'):
    emit(event, {'success': False, 'error': error}, room=request.sid)

def _is_agent_online(agent_id: int) -> bool:
    for sid in _connected_users:
        user_data = _connected_users.get(sid, None)
        if user_data.get("id", None) == agent_id:
            return True 
    return False

def _has_online_agent() -> bool:
    for sid in _connected_users:
        user_data = _connected_users.get(sid, None)
        if user_data.get("type", None) == "admin":
            return True
    return False

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
        "current_room": None,
        "id": current_user.id
    }

    join_room(ADMIN_ROOM)
    join_room(current_user.id)
    unaccommodated_clients = [serialize_client(client) for client in get_all_unassigned_clients()]
    emit('unaccommodated-clients', {'success': True, 'clients': unaccommodated_clients})
    emit(
        'clients-data',
        {
            'success': True,
            'clients': [serialize_client(client) for client in get_all_clients_assigned_to_agent(current_user.id)]
        },
        room=request.sid
    )


@socketio.on('disconnect')
def handle_disconnect():
    user = _connected_users.pop(request.sid, {})
    room_connected = user.get('current_room')

    if room_connected:
        emit('user-disconnected', {'success': True, 'uuid': room_connected}, room=ADMIN_ROOM)
        leave_room(room_connected)


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
    join_room(new_client.uuid)
    emit('new-client', {'success': True, 'client': serialize_client(new_client)}, room=request.sid)
    emit('new-client', {'success': True, 'client': serialize_client(new_client)}, room=ADMIN_ROOM)

    if not _has_online_agent():
        send_new_client_notification_to_al_agents(new_client.fullname)

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
    join_room(client_uuid)
    emit('validate-client-uuid', {'success': True}, room=request.sid)
    emit('get-history', {'success': True, 'messages': history}, room=request.sid)
    emit('user-connected', {'success': True, 'uuid': client_uuid}, room=ADMIN_ROOM)


@socketio.on('accept-client')
def handle_accept_client(data):
    client_uuid = data.get('client_uuid')

    user = _get_user()
    if not user:
        emit('accept-client', {'success': False, 'error': 'You are not connected.'})
        return

    if not _is_admin(user):
        emit('accept-client', {'success': False, 'error': 'You are not authorized to accept clients.'})
        return

    if not is_client_uuid_valid(client_uuid):
        emit('accept-client', {'success': False, 'error': 'Invalid client UUID.'})
        return

    client = LiveChatClient.query.filter_by(uuid=client_uuid).first()
    if not client:
        emit('accept-client', {'success': False, 'error': 'Client not found.'})
        return

    if is_client_assigned(client_uuid):
        emit('accept-client', {
            'success': False,
            'error': 'Client is already assigned to another agent.',
            'assigned_agent': client.agent.firstname
        })
        return

    client.agent_id = current_user.id
    db.session.commit()

    emit('accept-client', {'success': True, 'client': serialize_client(client)}, room=request.sid)
    emit(
        'client-assigned',
        {'success': True, 'client': serialize_client(client), 'agent': current_user.id},
        room=ADMIN_ROOM,
        include_self=False
    )


@socketio.on('get-history')
def handle_get_history(data):
    client_uuid = data.get('client_uuid')

    if not client_uuid:
        emit('get-history', {'success': False, 'error': 'Client UUID is required.'}, room=request.sid)
        return

    if not is_client_uuid_valid(client_uuid):
        emit('get-history', {'success': False, 'error': 'Invalid client UUID.'}, room=request.sid)
        return

    user = _get_user()
    if not _can_access_client(user, client_uuid):
        _deny('get-history')
        return

    history = get_message_history(client_uuid)
    mark_client_messages_read(client_uuid)
    client = LiveChatClient.query.filter_by(uuid=client_uuid).first()
    emit('get-history', {
        'success': True,
        'messages': history,
        'online': is_client_online(_connected_users, client_uuid),
        'is_ended': client.is_ended
    }, room=request.sid)
    join_room(client_uuid)


@socketio.on('read-message')
def handle_read_message(data):
    client_uuid = data.get('client_uuid')

    if not client_uuid:
        emit('read-message', {'success': False, 'error': 'Client UUID is required.'}, room=request.sid)
        return

    if not is_client_uuid_valid(client_uuid):
        emit('read-message', {'success': False, 'error': 'Invalid client UUID.'}, room=request.sid)
        return

    if not _is_admin(_get_user()):
        _deny('read-message')
        return

    mark_client_messages_read(client_uuid)
    emit('read-message', {'success': True}, room=request.sid)


@socketio.on('send-message')
def handle_send_message(data):
    client_uuid = data.get('client_uuid')
    content = data.get('content')

    if not client_uuid or not content:
        emit('send-message', {'success': False, 'error': 'Client UUID and content are required.'}, room=request.sid)
        return

    user = _get_user()
    if not user:
        emit('send-message', {'success': False, 'error': 'Not connected.'}, room=request.sid)
        return

    if not is_client_uuid_valid(client_uuid):
        emit('send-message', {'success': False, 'error': 'Invalid client UUID.'}, room=request.sid)
        return

    if user['type'] == 'client' and user.get('current_room') != client_uuid:
        emit('send-message', {'success': False, 'error': 'Unauthorized.'}, room=request.sid)
        return

    client = LiveChatClient.query.filter_by(uuid=client_uuid).first()
    if not client:
        emit('send-message', {'success': False, 'error': 'Client not found.'}, room=request.sid)
        return

    sender_type = 'agent' if user['type'] == 'admin' else 'client'
    message = Messages(
        client_id=client.id,
        sender=sender_type,
        content=content,
        content_type='text',
        unread=True
    )
    db.session.add(message)
    db.session.commit()

    payload = {'success': True, 'message': serialize_message(message)}

    if sender_type == 'client':
        emit('send-message', payload, room=request.sid)

        if client.agent_id:
            if _is_agent_online(client.agent_id) == False:
                send_message_notification(client.agent_id, client.fullname)
            emit('send-message', payload, room=client.agent_id)
        else:
            emit('send-message', payload, room=ADMIN_ROOM)
    else:
        emit('send-message', payload, room=client_uuid)


@socketio.on('delete-conversation')
def handle_delete_conversation(data):
    client_uuid = data.get('client_uuid')

    if not client_uuid:
        emit('delete-conversation', {'success': False, 'error': 'Client UUID is required.'}, room=request.sid)
        return

    if not is_client_uuid_valid(client_uuid):
        emit('delete-conversation', {'success': False, 'error': 'Invalid client UUID.'}, room=request.sid)
        return

    if not _is_admin(_get_user()):
        _deny('delete-conversation')
        return

    client = LiveChatClient.query.filter_by(uuid=client_uuid).first()
    if not client:
        emit('delete-conversation', {'success': False, 'error': 'Client not found.'}, room=request.sid)
        return

    messages = client.messages
    for message in messages:
        db.session.delete(message)
    db.session.delete(client)
    db.session.commit()

    emit('delete-conversation', {'success': True, 'client_uuid': client_uuid}, room=client_uuid)


@socketio.on('end-conversation')
def handle_end_conversation(data):
    client_uuid = data.get('client_uuid')

    if not client_uuid:
        emit('end-conversation', {'success': False, 'error': 'Client UUID is required.'}, room=request.sid)
        return

    if not is_client_uuid_valid(client_uuid):
        emit('end-conversation', {'success': False, 'error': 'Invalid client UUID.'}, room=request.sid)
        return

    if not _can_access_client(_get_user(), client_uuid):
        _deny('end-conversation')
        return

    client = LiveChatClient.query.filter_by(uuid=client_uuid, is_ended=False).first()
    if not client:
        emit('end-conversation', {'success': False, 'error': 'Client not found or already ended.'}, room=request.sid)
        return

    client.is_ended = True
    db.session.commit()

    emit('end-conversation', {'success': True, 'client_uuid': client_uuid}, room=client_uuid)