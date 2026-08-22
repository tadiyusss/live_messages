from datetime import datetime
from core.extensions import db
import uuid
import os

SENDER_CHOICES = ('client', 'agent')
CONTENT_TYPES = ('text', 'image', 'file')

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    client_id = db.Column(db.Integer, db.ForeignKey('live_chat_client.id'), nullable=False)
    client = db.relationship(
        'LiveChatClient',
        backref=db.backref('messages', lazy=True, cascade='all, delete-orphan'),
    )

    sender = db.Column(db.Enum(*SENDER_CHOICES, name='sender_choices'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.Enum(*CONTENT_TYPES, name='content_types'), nullable=False, default='text')
    unread = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def delete(self):
        if self.content_type in ['image', 'file']:
            file_path = os.path.join('media', self.content)
            if os.path.exists(file_path):
                os.remove(file_path)
        db.session.delete(self)
        db.session.commit()