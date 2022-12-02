from .database import db
from datetime import datetime


class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey(
        "service.id"), nullable=False)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False)
    image = db.Column(db.String)
    status = db.Column(db.String, nullable=False, default="PENDING")
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
