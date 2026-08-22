import os
import uuid

from flask import jsonify, request
from flask_login import current_user
from werkzeug.utils import secure_filename
from flask_login import login_required
from core.utils.decorators import roles_required
from core.extensions import db, socketio
from .. import bp
from ..forms.send_file import SendFileForm
from ..models import LiveChatClient, Messages
from ..utils.messages import serialize_client, serialize_message
from .sockets import ALLOWED_ROLES, ADMIN_ROOM, CONNECTED_USERS

IMAGE_EXTENSIONS = ('png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp')

@bp.route('/live-messages/upload', methods=['POST'])
@login_required
@roles_required(['Administrator', 'Support Agent'])
def upload_file():
    """
    Save an uploaded chat file to the media folder, record it as a message in the client's conversation, and broadcast it over sockets.
    """
    client_uuid = request.form.get('client_uuid')
    client = LiveChatClient.query.filter_by(uuid=client_uuid).first() if client_uuid else None
    if not client:
        return jsonify({'success': False, 'error': 'Invalid client UUID.'}), 400

    form = SendFileForm(meta={'csrf': False})
    if not form.validate():
        return jsonify({'success': False, 'error': 'Invalid file upload.', 'errors': form.errors}), 400

    user_roles = [user_role.role.name for user_role in current_user.user_roles] if current_user.is_authenticated else []
    sender = 'agent' if any(role in ALLOWED_ROLES for role in user_roles) else 'client'

    is_already_being_viewed = any(
        user.get('type') == 'admin' and user.get('current_room') == client_uuid
        for user in CONNECTED_USERS.values()
    )

    filename = secure_filename(form.file.data.filename) or 'file'
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    content_type = 'image' if extension in IMAGE_EXTENSIONS else 'file'

    if sender == 'client' and content_type == 'image':
        return jsonify({'success': False, 'error': 'Only support agents can send images.'}), 403

    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    if not os.path.exists('media'):
        os.makedirs('media')
    form.file.data.save(os.path.join('media', unique_filename))

    new_message = Messages(
        client_id=client.id,
        sender=sender,
        content=unique_filename,
        content_type=content_type,
        unread=sender == 'client' and not is_already_being_viewed
    )
    db.session.add(new_message)
    db.session.commit()

    socketio.emit('send_message', {
        'success': True,
        'messages': [serialize_message(new_message)]
    }, room=client_uuid)

    socketio.emit('sidebar_update', {
        'client': serialize_client(client),
    }, room=ADMIN_ROOM)

    return jsonify({'success': True, 'message': serialize_message(new_message)})
