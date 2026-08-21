from extensions.live_messages.models import LiveChatClient

def is_client_uuid_valid(uuid):
    return LiveChatClient.query.filter_by(uuid=uuid).first() is not None