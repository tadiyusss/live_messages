from core.extensions import socketio
from flask import request
from flask_login import current_user
from extensions.live_messages.forms.start_live_chat import StartLiveChatForm
from extensions.live_messages.models import LiveChatClient, Messages
from core.extensions import db
from flask_socketio import emit, join_room, leave_room
from extensions.live_messages.utils.messages import format_time, get_client_recent_message_data, is_client_uuid_valid, get_all_clients, get_unread_messages_count, mark_client_messages_read, get_message_history, serialize_client, serialize_message

ALLOWED_ROLES = ['Administrator', 'Support Agent']
CONNECTED_USERS = {}
ADMIN_ROOM = 'admins'

@socketio.on('connect')
def handle_connect():
    """
    Register the connecting socket as an admin or a client, sending admins the initial client list.
    """
    if not current_user.is_authenticated:
        CONNECTED_USERS[request.sid] = {
            'type': 'client',
            'user': None,
        }
        return

    user_roles = [user_role.role.name for user_role in current_user.user_roles]
    if not any(role in ALLOWED_ROLES for role in user_roles):
        return False

    clients = get_all_clients()
    clients_data = [serialize_client(client) for client in clients]
    CONNECTED_USERS[request.sid] = {
        'type': 'admin',
        'user': current_user,
        'current_room': None,
    }
    join_room(ADMIN_ROOM)
    emit('clients_data', {'clients': clients_data})


@socketio.on('disconnect')
def handle_disconnect():
    """
    Remove the disconnecting socket from the connected users registry.
    """
    CONNECTED_USERS.pop(request.sid, None)


@socketio.on('validate_client_uuid')
def handle_validate_client_uuid(data):
    """
    Validate a returning client's stored client_uuid, rejoin their room, and send their message history.
    """
    client_uuid = data.get('client_uuid')

    if not client_uuid or not is_client_uuid_valid(client_uuid):
        emit('validate_client_uuid', {'success': False})
        return

    emit('validate_client_uuid', {'success': True})
    join_room(client_uuid)

    connected_user = CONNECTED_USERS.get(request.sid)
    if connected_user is not None:
        connected_user['user'] = LiveChatClient.query.filter_by(uuid=client_uuid).first()

    emit('get_history', {
        'success': True,
        'messages': get_message_history(client_uuid)
    })


@socketio.on('get_history')
def handle_get_history(data):
    """
    Handle an admin request to load a client's message history, switch that admin's active room, and mark the conversation as read.
    """
    client_uuid = data.get('client_uuid')

    client = LiveChatClient.query.filter_by(uuid=client_uuid).first() if client_uuid else None
    if not client:
        emit('get_history', {
            'success': False,
            'error': 'Invalid client UUID.'
        })
        return

    connected_user = CONNECTED_USERS.get(request.sid)
    if connected_user is not None and connected_user['type'] == 'admin':
        current_room = connected_user.get('current_room')
        if current_room:
            leave_room(current_room)
        join_room(client_uuid)
        connected_user['current_room'] = client_uuid

        mark_client_messages_read(client_uuid)
        emit('sidebar_update', {'client': serialize_client(client)}, room=ADMIN_ROOM)

    emit('get_history', {
        'success': True,
        'messages': get_message_history(client_uuid)
    })


@socketio.on('start_chat')
def handle_start_chat(data):
    """
    Handle StartLiveChatForm submission from the client, create a new LiveChatClient if valid, and announce it to the admin sidebar.
    """
    form = StartLiveChatForm(data=data, meta={'csrf': False})
    if not form.validate():
        emit('start_chat', {
            'success': False,
            'errors': form.errors
        })
        return

    new_client = LiveChatClient(
        fullname=form.fullname.data,
        email=form.email.data,
        phone_number=form.phone_number.data
    )
    db.session.add(new_client)
    db.session.commit()
    join_room(new_client.uuid)

    connected_user = CONNECTED_USERS.get(request.sid)
    if connected_user is not None:
        connected_user['user'] = new_client

    emit('start_chat', {
        'success': True,
        'client_uuid': new_client.uuid
    })

    emit('sidebar_update', {
        'client': serialize_client(new_client),
    }, room=ADMIN_ROOM)


@socketio.on('send_message')
def handle_send_message(data):
    """
    Handle a message sent by either an admin or a client, broadcast it to everyone in that client's room, and refresh the admin sidebar.
    """
    client_uuid = data.get('client_uuid')
    content = data.get('content')
    content_type = data.get('content_type', 'text')

    if not client_uuid or not is_client_uuid_valid(client_uuid):
        emit('send_message', {
            'success': False,
            'error': 'Invalid client UUID.'
        })
        return

    if not content:
        emit('send_message', {
            'success': False,
            'error': 'Message content is required.'
        })
        return

    connected_user = CONNECTED_USERS.get(request.sid, {})
    sender = 'agent' if connected_user.get('type') == 'admin' else 'client'
    client = LiveChatClient.query.filter_by(uuid=client_uuid).first()
    is_already_being_viewed = any(
        user.get('type') == 'admin' and user.get('current_room') == client_uuid
        for user in CONNECTED_USERS.values()
    )

    new_message = Messages(
        client_id=client.id,
        sender=sender,
        content=content,
        content_type=content_type,
        unread=sender == 'client' and not is_already_being_viewed
    )
    db.session.add(new_message)
    db.session.commit()

    emit('send_message', {
        'success': True,
        'messages': [serialize_message(new_message)]
    }, room=client_uuid)

    emit('sidebar_update', {
        'client': serialize_client(client),
    }, room=ADMIN_ROOM)