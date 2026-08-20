from core.extensions import socketio
from flask import request
from flask_login import current_user

@socketio.on('connect')
def handle_new_connection():
    if current_user.is_authenticated:
        socketio.emit('user_connected', {'user_id': current_user.id, 'username': current_user.username})
    else:
        socketio.emit('user_connected', {'user_id': None, 'username': 'Anonymous'})

