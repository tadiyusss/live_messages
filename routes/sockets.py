from core.extensions import socketio
from flask import request
from flask_login import current_user
from extensions.live_messages.forms.start_live_chat import StartLiveChatForm
from extensions.live_messages.models import LiveChatClient, Messages
from core.extensions import db
from flask_socketio import emit, join_room
from extensions.live_messages.utils.messages import format_time, get_client_recent_message_data, is_client_uuid_valid, get_all_clients

ALLOWED_ROLES = ['Administrator', 'Support Agent']
CONNECTED_USERS = {}

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        user_roles = [user_role.role.name for user_role in current_user.user_roles]
        if any(role in ALLOWED_ROLES for role in user_roles):
            clients = get_all_clients()
            clients_data_and_messages = [
                {
                    'uuid': client.uuid,
                    'fullname': client.fullname,
                    'email': client.email,
                    'phone_number': client.phone_number,
                    'last_message': get_client_recent_message_data(client.uuid)
                }
                for client in clients
            ]
            CONNECTED_USERS[request.sid] = {
                "type": "admin",
                "user": None if current_user.is_anonymous else current_user,
            }
            emit('clients_data', {'clients': clients_data_and_messages})
        else:
            return False
    else:
        CONNECTED_USERS[request.sid] = {
            "type": "client",
            "user": None,
        }

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in CONNECTED_USERS:
        del CONNECTED_USERS[request.sid]

@socketio.on('validate_client_uuid')
def handle_validate_client_uuid(data):
    """
    Check if the provided client_uuid is valid on the database.
    """
    client_uuid = data.get('client_uuid')
    if client_uuid and is_client_uuid_valid(client_uuid):
        emit('validate_client_uuid', {'success': True})
        join_room(client_uuid)
        messages = Messages.query.join(LiveChatClient).filter(LiveChatClient.uuid == client_uuid).order_by(Messages.created_at.asc()).all()
        messages_data = [
            {
                'content': msg.content,
                'content_type': msg.content_type,
                'sender': msg.sender,
                'uuid': msg.uuid,
                'name': msg.client.fullname,
                'time': msg.created_at.strftime('%I:%M %p')
            }
            for msg in messages
        ]
        connected_user = CONNECTED_USERS.get(request.sid)
        if connected_user and connected_user["type"] == "client":
            connected_user["user"] = LiveChatClient.query.filter_by(uuid=client_uuid).first()
        emit('receive_message', {'messages': messages_data})
    else:
        emit('validate_client_uuid', {'success': False})

@socketio.on('get_history')
def handle_get_history(data):
    """
    Handle request to get message history for a specific client.
    """
    client_uuid = data.get('client_uuid')
    print(client_uuid)

    if not client_uuid or not is_client_uuid_valid(client_uuid):
        emit('get_history', {
            'success': False,
            'error': 'Invalid client UUID.'
        })
        return

    messages = Messages.query.join(LiveChatClient).filter(LiveChatClient.uuid == client_uuid).order_by(Messages.created_at.asc()).all()
    messages_data = [
        {
            'content': msg.content,
            'content_type': msg.content_type,
            'sender': msg.sender,
            'uuid': msg.uuid,
            'name': msg.client.fullname,
            'created_at': format_time(msg.created_at)
        }
        for msg in messages
    ]

    emit('get_history', {
        'success': True,
        'messages': messages_data
    })

@socketio.on('start_chat')
def handle_start_chat(data):
    """
    Handle StartLiveChatForm submission from the client. Validate the form and create a new LiveChatClient if valid.
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
        join_room(new_client.uuid)

        emit('start_chat', {
            'success': True,
            'client_uuid': new_client.uuid
        })

    else:

        emit('start_chat', {
            'success': False,
            'errors': form.errors
        })

@socketio.on('send_message')
def handle_send_message(data):
    """"
    Handle sending messages from client. 
    """

    content = data.get('content')
    content_type = data.get('content_type', 'text')
    client_uuid = data.get('client_uuid')
    sender = 'client'

    if not client_uuid or not is_client_uuid_valid(client_uuid):
        emit('send_message', {
            'success': False,
            'error': 'Invalid client UUID.'
        })
        return

    if not content:
        emit('send_message', {
            'success': False,
            'error': 'Content and content type are required.'
        })
        return

    new_message = Messages(
        client_id=LiveChatClient.query.filter_by(uuid=client_uuid).first().id,
        sender=sender,
        content=content,
        content_type=content_type
    )
    db.session.add(new_message)
    db.session.commit()

    emit('send_message', {
        'success': True,
    })

    emit('receive_message', {
        'messages': [
            {
            'content': new_message.content,
            'content_type': new_message.content_type,
            'sender': new_message.sender,
            'uuid': new_message.uuid,
            'name': new_message.client.fullname,
            'time': new_message.created_at.strftime('%I:%M %p')
            }
        ]
    })