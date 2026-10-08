import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from .database import Base

class Project(Base):
    __tablename__ = "projects"

    # UUIDs (unique text strings) instead of 1, 2, 3 for better security
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    url = Column(String, nullable=False)
    secret = Column(String, nullable=False) # Used later to securely sign the webhooks
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False) # Stores the actual data for eg - {"order_id": 123}
    idempotency_key = Column(String, nullable=False) # Prevents saving the same event twice
    created_at = Column(DateTime, default=datetime.utcnow)

class DeadLetter(Base):
    __tablename__ = "dead_letters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String)
    endpoint_url = Column(String)
    payload = Column(JSON)
    error_message = Column(String)
    failed_at = Column(DateTime, default=datetime.utcnow)