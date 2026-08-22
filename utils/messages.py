from extensions.live_messages.models import LiveChatClient
from extensions.live_messages.models import Messages
from core.extensions import db
from datetime import datetime, timedelta
def is_client_uuid_valid(uuid):
    return LiveChatClient.query.filter_by(uuid=uuid).first() is not None

def format_time(dt):
    if dt.date() == datetime.now().date():
        return dt.strftime('%I:%M %p')
    elif dt.date() == (datetime.now() - timedelta(days=1)).date():
        return 'Yesterday'
    elif dt.date() > (datetime.now() - timedelta(days=7)).date():
        return dt.strftime('%A')
    else:
        return dt.strftime('%b %d, %Y')


def get_all_clients():
    return LiveChatClient.query.all()

def get_unread_messages_count(client_uuid):
    return Messages.query.join(LiveChatClient).filter(LiveChatClient.uuid == client_uuid, Messages.unread.is_(True)).count()

def mark_client_messages_read(client_uuid):
    client = LiveChatClient.query.filter_by(uuid=client_uuid).first()
    if not client:
        return
    Messages.query.filter_by(client_id=client.id, unread=True).update({'unread': False})
    db.session.commit()

def get_file_display_name(filename):
    return filename.split('_', 1)[1] if '_' in filename else filename

def get_client_recent_message_data(client_uuid):
    client = LiveChatClient.query.filter_by(uuid=client_uuid).first()
    if not client:
        return None

    last_message = client.last_message
    if not last_message:
        return None

    content = last_message.content
    if last_message.content_type in ('image', 'file'):
        content = get_file_display_name(content)

    return {
        'content': content,
        'content_type': last_message.content_type,
        'created_at': format_time(last_message.created_at)
    }

def serialize_message(message):
    """
    Build the message payload shared by every socket route that sends message data to the frontend.
    """
    return {
        'uuid': message.uuid,
        'client_uuid': message.client.uuid,
        'sender': message.sender,
        'name': 'Support' if message.sender == 'agent' else message.client.fullname,
        'content': message.content,
        'content_name': get_file_display_name(message.content) if message.content_type in ('image', 'file') else message.content,
        'content_type': message.content_type,
        'created_at': format_time(message.created_at),
    }

def get_message_history(client_uuid):
    """
    Fetch and serialize the full message history for a client, oldest first.
    """
    messages = Messages.query.join(LiveChatClient).filter(LiveChatClient.uuid == client_uuid).order_by(Messages.created_at.asc()).all()
    return [serialize_message(message) for message in messages]

def serialize_client(client):
    """
    Build the sidebar payload for a client, shared by the initial admin connection and live sidebar updates.
    """
    return {
        'uuid': client.uuid,
        'fullname': client.fullname,
        'email': client.email,
        'phone_number': client.phone_number,
        'last_message': get_client_recent_message_data(client.uuid),
        'unread_count': get_unread_messages_count(client.uuid),
    }
