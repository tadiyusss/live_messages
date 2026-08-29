from core.extensions import socketio
from flask import request
from flask_login import current_user
from extensions.live_messages.forms.start_live_chat import StartLiveChatForm
from extensions.live_messages.models import LiveChatClient, Messages
from core.extensions import db
from flask_mail import Message
from core.extensions import mail
from flask_socketio import emit, join_room, leave_room
from extensions.live_messages.utils.messages import is_client_uuid_valid, get_all_clients, mark_client_messages_read, get_message_history, serialize_client, serialize_message
from core.models.users import User, Role, UserRole

ALLOWED_ROLES = ['Administrator', 'Support Agent']
_connected_users = dict()

@socketio.on('connect')
def handle_connect():
    """
    Handle a new socket connection. If the user is logged in and has the appropriate role, add them to the admin room and track their connection.
    """

    if not current_user.is_authenticated:
        _connected_users[request.sid] = {
            "type": "client",
            "current_room": None
        }
        print(f"Anonymous Client Connected: {request.sid}")
        return

    if any(role.role.name in ALLOWED_ROLES for role in current_user.user_roles):
        _connected_users[request.sid] = {
            "type": "agent",
            "current_room": None
        }
        print(f"Agent Connected: {current_user.username} (SID: {request.sid})")
        return

    
    