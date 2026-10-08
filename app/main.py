import secrets
import json
import redis
import os
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session


from app.models import database, models
from app.api import schemas

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Webhook Delivery Platform")

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

@app.get("/v1/health")
def health_check():
    return {"status": "ok", "message": "Webhook platform is up and running"}

@app.post("/v1/endpoints", response_model=schemas.EndpointResponse)
def register_webhook(endpoint: schemas.EndpointCreate, db: Session = Depends(database.get_db)):
    project = db.query(models.Project).filter(models.Project.id == endpoint.project_id).first()
    if not project:
        new_project = models.Project(id=endpoint.project_id, name=f"Auto-generated {endpoint.project_id}")
        db.add(new_project)
        db.commit()

    webhook_secret = f"whsec_{secrets.token_hex(16)}"
    new_endpoint = models.WebhookEndpoint(
        project_id=endpoint.project_id,
        url=endpoint.url,
        secret=webhook_secret
    )
    db.add(new_endpoint)
    db.commit()
    db.refresh(new_endpoint)
    return new_endpoint

@app.post("/v1/events", response_model=schemas.EventResponse)
def publish_event(event: schemas.EventCreate, db: Session = Depends(database.get_db)):
    new_event = models.Event(
        project_id=event.project_id,
        event_type=event.event_type,
        payload=event.payload,
        idempotency_key=event.idempotency_key
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    endpoints = db.query(models.WebhookEndpoint).filter(
        models.WebhookEndpoint.project_id == event.project_id,
        models.WebhookEndpoint.active == True
    ).all()

    for endpoint in endpoints:
        job = {
            "event_id": new_event.id,
            "endpoint_url": endpoint.url,
            "payload": new_event.payload,
            "secret": endpoint.secret
        }
        redis_client.lpush("webhook_queue", json.dumps(job))
    
    return new_event