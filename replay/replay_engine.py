import time
from pathlib import Path
from datetime import datetime, timedelta

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_INPUT_FILE = (
    PROJECT_ROOT / "data" / "raw" / "HDFS.log"
)


# ---------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------

def parse_timestamp(line):
    """
    Parse timestamp from an HDFS log line.

    HDFS format:

        YYMMDD HHMMSS PID LEVEL COMPONENT: MESSAGE

    Example:

        081109 203518 143 INFO dfs.DataNode$DataXceiver: ...
    """

    parts = line.split()

    if len(parts) < 2:
        return None

    try:
        return datetime.strptime(
            parts[0] + parts[1],
            "%y%m%d%H%M%S"
        )

    except ValueError:
        return None


# ---------------------------------------------------------
# Timestamp replacement
# ---------------------------------------------------------

def replace_timestamp(line, new_timestamp):
    """
    Replace only the original date and time.

    Everything else in the log line remains unchanged.
    """

    parts = line.split(maxsplit=2)

    if len(parts) < 3:
        return line

    new_date = new_timestamp.strftime("%y%m%d")
    new_time = new_timestamp.strftime("%H%M%S")

    return f"{new_date} {new_time} {parts[2]}"


# ---------------------------------------------------------
# Replay generator
# ---------------------------------------------------------

def replay_log(
    input_file=DEFAULT_INPUT_FILE,
    speed=100.0,
    replay_start_time=None,
    max_lines=None
):
    """
    Continuously replay historical HDFS logs.

    When the end of the file is reached, replay starts again
    from the beginning while the replay timestamp continues
    forward.
    """

    input_file = Path(input_file)

    if not input_file.exists():
        raise FileNotFoundError(
            f"HDFS log file not found: {input_file}"
        )

    if speed <= 0:
        raise ValueError(
            "Replay speed must be greater than 0."
        )

    if replay_start_time is None:
        replay_start_time = datetime.now()

    # Read valid log lines once so we can replay them repeatedly.
    valid_lines = []

    with input_file.open(
        "r",
        encoding="utf-8",
        errors="replace"
    ) as file:

        for line in file:

            line = line.rstrip("\n")

            if not line:
                continue

            timestamp = parse_timestamp(line)

            if timestamp is None:
                continue

            valid_lines.append(
                (line, timestamp)
            )

    if not valid_lines:
        raise ValueError(
            "No valid HDFS log lines found."
        )

    # Original duration of one complete replay cycle.
    first_timestamp = valid_lines[0][1]
    last_timestamp = valid_lines[-1][1]

    cycle_duration = (
        last_timestamp - first_timestamp
    )

    cycle_start_time = replay_start_time

    while True:

        previous_timestamp = None

        for line, timestamp in valid_lines:

            # Replay timing inside the current cycle.
            if previous_timestamp is not None:

                time_difference = (
                    timestamp - previous_timestamp
                ).total_seconds()

                if time_difference > 0:

                    delay = (
                        time_difference / speed
                    )

                    time.sleep(delay)

            elapsed_time = (
                timestamp - first_timestamp
            )

            replay_timestamp = (
                cycle_start_time + elapsed_time
            )

            replayed_line = replace_timestamp(
                line,
                replay_timestamp
            )

            yield replayed_line

            previous_timestamp = timestamp

        # Move the replay clock forward for the
        # next complete replay cycle.
        cycle_start_time += (
            cycle_duration + timedelta(seconds=1)
        )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":

    replay_start = datetime.now()

    for replayed_line in replay_log(
        input_file=DEFAULT_INPUT_FILE,
        speed=100.0,
        replay_start_time=replay_start,
        max_lines=100
    ):
        print(
            replayed_line,
            flush=True
        )