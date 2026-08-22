from datetime import datetime
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="HDFS Log Analytics API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


lock = Lock()

active_anomalies = {}
resolved_anomalies = []
recent_events = []
total_blocks = set()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "hdfs-log-analytics",
    }


@app.get("/api/dashboard")
def dashboard():

    with lock:
        return {
            "total_blocks": len(total_blocks),
            "active_anomalies": list(
                active_anomalies.values()
            ),
            "resolved_anomalies": resolved_anomalies,
            "recent_events": recent_events[-50:],
        }


@app.post("/api/blocks/{block_id}/resolve")
def resolve_anomaly(block_id: str):

    with lock:

        anomaly = active_anomalies.pop(
            block_id,
            None
        )

        if anomaly is None:
            raise HTTPException(
                status_code=404,
                detail="Active anomaly not found",
            )

        anomaly = {
            **anomaly,
            "status": "resolved",
            "resolved_at": datetime.now().isoformat(),
        }

        resolved_anomalies.append(anomaly)

        return {
            "status": "resolved",
            "block_id": block_id,
        }


def register_block(block_id):
    if not block_id:
        return

    with lock:
        total_blocks.add(block_id)


def register_event(event):
    with lock:

        recent_events.append(event)

        if len(recent_events) > 50:
            del recent_events[:-50]


def register_anomaly(anomaly):
    """
    Create or update an active anomaly.

    If the same block is already active,
    don't create a duplicate alert.
    """

    block_id = anomaly["block_id"]

    with lock:

        total_blocks.add(block_id)

        if block_id in active_anomalies:
            active_anomalies[block_id].update(
                anomaly
            )
            return False

        active_anomalies[block_id] = {
            **anomaly,
            "status": "active",
            "detected_at": datetime.now().isoformat(),
        }

        return True

from fastapi import Body

@app.post("/api/events")
def receive_event(event: dict = Body(...)):

    block_id = event.get("block_id")

    if block_id:
        register_block(block_id)

    register_event(event)

    return {
        "status": "received"
    }


@app.post("/api/anomalies")
def receive_anomaly(anomaly: dict = Body(...)):

    created = register_anomaly(anomaly)

    return {
        "status": "received",
        "created": created,
        "block_id": anomaly.get("block_id")
    }

def start_api():
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="warning",
    )