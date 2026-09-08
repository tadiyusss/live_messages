from ..models import LiveChatClient

def get_active_live_chat_client_count(current_user):
    """
    Get the count of active live chat clients for the current user.
    """
    return LiveChatClient.query.filter_by(agent_id=current_user.id, is_ended=False).count()

def get_unread_messages_count(current_user):
    """
    Get the count of unread messages for the current user.
    """
    clients = LiveChatClient.query.filter_by(agent_id=current_user.id, is_ended=False).all()
    unread_count = 0
    for client in clients:
        unread_count += client.unread_messages_count
    return unread_count

def unaccepted_live_chat_clients_count():
    """
    Get the count of unaccepted live chat clients on the platform.
    """
    return LiveChatClient.query.filter_by(agent_id=None, is_ended=False).count()