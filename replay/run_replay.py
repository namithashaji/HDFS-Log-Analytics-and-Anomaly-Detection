import sys
import os
from pathlib import Path
from collections import deque
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from replay_engine import replay_log
from replay_processor import ReplayProcessor
from inference.sequence_builder import SequenceBuilder
from inference.predictor import LSTMPredictor
from inference.alert_manager import AlertManager

import json
from urllib.request import Request, urlopen
from urllib.error import URLError

API_URL = "http://127.0.0.1:8000"

def send_to_api(endpoint, data):

    try:
        payload = json.dumps(data).encode("utf-8")

        request = Request(
            f"{API_URL}{endpoint}",
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        with urlopen(request, timeout=2) as response:
            return response.read()

    except URLError as error:

        print(
            f"[API ERROR] "
            f"Could not send data to {endpoint}: {error}"
        )

        return None


def send_event_to_api(event):

    send_to_api(
        "/api/events",
        event
    )


def send_anomaly_to_api(anomaly):

    send_to_api(
        "/api/anomalies",
        anomaly
    )

# Monitoring configuration
WINDOW_MINUTES = 10
CHECK_INTERVAL_MINUTES = 5
MAX_SEQUENCE_LENGTH = 298


def get_event_timestamp(parsed_event):
    return datetime.strptime(
        f"{parsed_event['Date']} {parsed_event['Time']}",
        "%y%m%d %H%M%S"
    )


def evaluate_window(
    window_events,
    predictor,
    alert_manager
):
    """
    Run anomaly detection on all BlockId sequences
    present in the current 5-minute window.
    """

    if not window_events:
        return

    # Build fresh sequences for THIS monitoring window.
    window_builder = SequenceBuilder(
        max_length=MAX_SEQUENCE_LENGTH
    )

    latest_events = {}

    for event in window_events:

        block_id = event.get("BlockId")

        if not block_id:
            continue

        sequence = window_builder.add_event(event)

        if sequence is None:
            continue

        latest_events[block_id] = event

    sequences = window_builder.get_all_sequences()

    print(
        f"\n[WINDOW CHECK] "
        f"Blocks analyzed: {len(sequences)}"
    )

    for block_id, sequence in sequences.items():

        result = predictor.predict(sequence)

        should_alert = alert_manager.process_prediction(
            block_id,
            result
        )

        # If this prediction should not create a new alert,
        # continue to the next block.
        if not should_alert:
            continue

        event = latest_events[block_id]

        probability = result["probability"]

        # Send anomaly to FastAPI backend.
        send_anomaly_to_api(
            {
                "block_id": block_id,
                "component": event.get(
                    "Component",
                    "Unknown"
                ),
                "probability": probability * 100,
                "sequence_length": len(sequence),
                "time": (
                    f"{event['Date']} "
                    f"{event['Time']}"
                ),
                "message": event.get(
                    "Message",
                    ""
                ),
            }
        )

        # Console output
        print("\n" + "=" * 60)
        print("ANOMALY DETECTED")
        print("=" * 60)

        print(
            f"Time:        "
            f"{event['Date']} {event['Time']}"
        )

        print(
            f"Block ID:    "
            f"{block_id}"
        )

        print(
            f"Component:   "
            f"{event['Component']}"
        )

        print(
            f"Probability: "
            f"{probability:.4f}"
        )

        print(
            f"Sequence:    "
            f"{len(sequence)} events"
        )

        print(
            f"Message:     "
            f"{event['Message']}"
        )

        print("=" * 60)


def run():

    processor = ReplayProcessor()
    predictor = LSTMPredictor()
    alert_manager = AlertManager()

    # Events currently inside the rolling 5-minute window.
    window_events = deque()

    next_check_time = None

    for replayed_line in replay_log(
        speed=1.0,
    ):

        parsed_event = processor.parse_line(
            replayed_line
        )

        if parsed_event is None:
            continue

        event_time = get_event_timestamp(
            parsed_event
        )

        block_id = parsed_event.get("BlockId")

        send_event_to_api(
            {
                "time": (
                    f"{parsed_event['Date']} "
                    f"{parsed_event['Time']}"
                ),
                "block_id": block_id,
                "component": parsed_event.get(
                    "Component",
                    "Unknown"
                ),
                "message": parsed_event.get(
                    "Message",
                    ""
                ),
            }
        )

        # Add current event to rolling window.
        window_events.append(
            (
                event_time,
                parsed_event
            )
        )

        # Remove events older than 5 minutes.
        window_start = (
            event_time
            - timedelta(minutes=WINDOW_MINUTES)
        )

        while (
            window_events
            and window_events[0][0] < window_start
        ):
            window_events.popleft()

        # First check happens after the first
        # complete 5-minute monitoring window.
        if next_check_time is None:
            next_check_time = (
                event_time
                + timedelta(minutes=WINDOW_MINUTES)
            )
            continue

        # Check every 1 minute.
        if event_time >= next_check_time:

            current_window = [
                event
                for _, event in window_events
            ]

            evaluate_window(
                current_window,
                predictor,
                alert_manager
            )

            next_check_time += timedelta(
                minutes=CHECK_INTERVAL_MINUTES
            )


if __name__ == "__main__":
    run()