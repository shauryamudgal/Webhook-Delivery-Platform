from pydantic import BaseModel
from typing import Dict, Any

class EndpointCreate(BaseModel):
    project_id: str
    url: str

class EndpointResponse(BaseModel):
    id: str
    project_id: str
    url: str
    active: bool

class EventCreate(BaseModel):
    project_id: str
    event_type: str
    payload: Dict[str, Any]
    idempotency_key: str

class EventResponse(BaseModel):
    id: str
    project_id: str
    event_type: str
    idempotency_key: str

    class Config:
        from_attributes = True

