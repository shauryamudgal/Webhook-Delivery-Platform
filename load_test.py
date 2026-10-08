import asyncio
import httpx
import time
import uuid

API_URL = "http://127.0.0.1:8000/v1/events"
TOTAL_REQUESTS = 1000
CONCURRENCY = 20

payload = {
    "project_id": "live_test",
    "event_type": "load.test",
    "payload": {"status": "testing", "metric": "percentiles"}
}

async def send_request(client):
    event_payload = payload.copy()
    event_payload["idempotency_key"] = str(uuid.uuid4())
    
    start_time = time.time()
    try:
        response = await client.post(API_URL, json=event_payload)
        status_code = response.status_code
    except Exception:
        status_code = 500
        
    end_time = time.time()
    
    return status_code, (end_time - start_time) * 1000

async def main():
    print(f"🚀 Firing {TOTAL_REQUESTS} events to calculate p99 latency...")
    
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=CONCURRENCY), timeout=timeout) as client:
        start_time = time.time()
        
        tasks = [send_request(client) for _ in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
    successes = sum(1 for status, _ in results if status == 200)
    
    latencies = [latency for status, latency in results if status == 200]
    
    if latencies:
        latencies.sort() # Sort from fastest to slowest
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
    else:
        p50 = p95 = p99 = 0
        
    print("\n📊 --- LATENCY METRICS ---")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Throughput: {successes / total_time:.0f} RPS")
    print(f"Median (p50): {p50:.2f} ms")
    print(f"p95 Latency:  {p95:.2f} ms")
    print(f"p99 Latency:  {p99:.2f} ms")

if __name__ == "__main__":
    asyncio.run(main())