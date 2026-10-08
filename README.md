# Enterprise Webhook Delivery Platform

A robust, production-grade asynchronous webhook dispatch system built with Python and FastAPI. This platform is designed to decouple event ingestion from HTTP delivery, ensuring high availability, fault tolerance, and cryptographic security for outbound webhooks.

## Architecture Overview

The system utilizes a decoupled micro-architecture to prevent slow outbound network requests from blocking the main API thread:

1. **Ingestion Layer (FastAPI):** Instantly validates and durably stores incoming events in PostgreSQL.
2. **Message Broker (Redis):** Queues delivery jobs for asynchronous processing.
3. **Delivery Worker (Python):** A standalone background process that watches the queue, signs the payloads, and reliably dispatches them across the network.

## Key Features

* **Asynchronous Processing:** Utilizes a Redis-backed queue (`brpop`) and decoupled workers to process deliveries outside the API request cycle.
* **Cryptographic Security:** Secures all outbound payloads with an HMAC-SHA256 signature attached to the `Webhook-Signature` header, allowing consumers to verify data integrity.
* **Fault Tolerance & Exponential Backoff:** Automatically detects network failures or offline destination servers, retrying deliveries with exponentially increasing delays (2s, 4s, 8s) to prevent network flooding.
* **Dead Letter Queue (DLQ):** Prevents data loss by intercepting permanently failed jobs (after max retries) and durably burying them in a dedicated PostgreSQL `dead_letters` table for future inspection.
* **Fully Containerized:** Orchestrated via Docker Compose for seamless, reproducible, one-click deployments.

## Tech Stack

* **API Framework:** FastAPI, Uvicorn
* **Database / ORM:** PostgreSQL, SQLAlchemy
* **Message Broker:** Redis
* **HTTP Client:** HTTPX
* **Infrastructure:** Docker, Docker Compose

## Quickstart

The entire ecosystem (Database, Redis, API, and Worker) is containerized and ready to launch.

1. **Clone the repository and start the cluster:**

   ```bash
   git clone https://github.com/yourusername/webhook-platform.git
   cd webhook-platform
   docker compose up --build
   ```

2. **Access the API Documentation:**

   Open your browser and navigate to the interactive Swagger UI at:

   `http://localhost:8000/docs`

## Usage Guide

### 1. Register a Webhook Endpoint

Register a destination URL to receive events. The system will automatically generate a secure `whsec_...` secret for this endpoint.

**POST** `/v1/endpoints`

```json
{
  "project_id": "demo_project",
  "url": "https://webhook.site/your-unique-id"
}
```

### 2. Publish an Event

Fire an event into the system. The API will immediately return a `200 OK`, while the background worker handles the actual delivery, signing, and potential retries.

**POST** `/v1/events`

```json
{
  "project_id": "demo_project",
  "event_type": "user.created",
  "payload": {
    "user_id": 12345,
    "email": "engineer@example.com"
  },
  "idempotency_key": "req_88321a"
}
```

### 3. Verify the Signature (Consumer Side)

When the destination server receives the payload, it can verify authenticity by calculating the HMAC-SHA256 hash of the raw JSON body using its secret, and comparing it to the:

`Webhook-Signature: v1=<hash>`

## Performance Benchmarks

The platform was subjected to stress testing using an asynchronous Python load testing script (`load_test.py`) simulating concurrent event spikes against the containerized cluster:

* **Throughput:** 171 Requests Per Second (RPS)
* **p99 Latency:** 5.49 ms (across 1,000 concurrent payloads)
* **Success Rate:** 100% (zero dropped connections, utilizing exponential backoff and DLQ fallback)

header.