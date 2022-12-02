from .database import db
from datetime import datetime


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    service_type = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, default="ACTIVE")
    location = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
