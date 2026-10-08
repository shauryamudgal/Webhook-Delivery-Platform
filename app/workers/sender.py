import json
import redis
import httpx
import hmac
import hashlib
import time
import os

# NEW: Import your database connection and DLQ model
from app.models.database import SessionLocal
from app.models.models import DeadLetter

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

print("🚚 Delivery Worker started. Waiting for jobs on the conveyor belt...")

MAX_RETRIES = 3

while True:
    result = redis_client.brpop("webhook_queue", timeout=2)
    
    if not result:
        continue
        
    queue_name, job_data = result
    job = json.loads(job_data)
    
    print(f"\n📦 Found job! Delivering event {job['event_id']} to {job['endpoint_url']}")
    
    payload_string = json.dumps(job['payload'], separators=(',', ':'))
    
    signature = hmac.new(
        key=job['secret'].encode('utf-8'),
        msg=payload_string.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Webhook-Signature": f"v1={signature}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = httpx.post(
                job['endpoint_url'], 
                content=payload_string, 
                headers=headers,
                timeout=5.0
            )
            
            if 200 <= response.status_code < 300:
                print(f"✅ Success on attempt {attempt}! Server replied with {response.status_code}")
                break
            else:
                print(f"⚠️ Attempt {attempt} failed: Server returned {response.status_code}")
                
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {str(e)}")
            
        if attempt < MAX_RETRIES:
            wait_time = 2 ** attempt
            print(f"⏳ Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
        else:
            # --- NEW: Save to Dead Letter Queue ---
            print("🚨 Max retries reached. Moving to Dead Letter Queue (DLQ)...")
            db = SessionLocal()
            try:
                dlq_entry = DeadLetter(
                    event_id=job['event_id'],
                    endpoint_url=job['endpoint_url'],
                    payload=job['payload'],
                    error_message=f"Failed after {MAX_RETRIES} attempts"
                )
                db.add(dlq_entry)
                db.commit()
                print("🪦 Job safely buried in DLQ.")
            except Exception as db_err:
                print(f"❌ Failed to save to DLQ: {str(db_err)}")
            finally:
                db.close() # Always close the database connection when done