from datetime import datetime
from core.extensions import db
import uuid

class LiveChatClient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(11), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)