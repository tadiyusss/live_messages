from extensions.live_messages.models import LiveChatClient
from extensions.live_messages.models import Messages
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

def get_client_recent_message_data(client_uuid):
    client = LiveChatClient.query.filter_by(uuid=client_uuid).first()
    if not client:
        return None

    last_message = client.last_message
    if not last_message:
        return None

    return {
        'content': last_message.content,
        'content_type': last_message.content_type,
        'created_at': format_time(last_message.created_at)
    }