import json
import re
from pathlib import Path


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MAPPING_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "event_mapping.json"
)


# ---------------------------------------------------------
# Replay Processor
# ---------------------------------------------------------

class ReplayProcessor:

    def __init__(
        self,
        event_mapping_path=DEFAULT_MAPPING_FILE
    ):
        """
        Load the SAME event mapping used during training.
        """

        event_mapping_path = Path(event_mapping_path)

        if not event_mapping_path.exists():
            raise FileNotFoundError(
                f"Event mapping not found: "
                f"{event_mapping_path}"
            )

        with event_mapping_path.open(
            "r",
            encoding="utf-8"
        ) as file:

            self.event_mapping = json.load(file)

        print(
            f"Loaded "
            f"{len(self.event_mapping)} event templates"
        )

    # -----------------------------------------------------
    # Message normalization
    # -----------------------------------------------------

    def normalize_message(self, message):
        """
        Normalize an HDFS message using the SAME
        preprocessing logic used during training.
        """

        # Replace HDFS block IDs
        message = re.sub(
            r"blk_-?\d+",
            "<BLOCK>",
            message
        )

        # Replace IP addresses and optional ports
        message = re.sub(
            r"\d+\.\d+\.\d+\.\d+(?::\d+)?",
            "<IP>",
            message
        )

        # Replace file paths
        message = re.sub(
            r"/[\w./:-]+",
            "<PATH>",
            message
        )

        # Replace standalone numbers
        message = re.sub(
            r"\b\d+\b",
            "<NUM>",
            message
        )

        return message

    # -----------------------------------------------------
    # Event ID conversion
    # -----------------------------------------------------

    def get_event_id(self, normalized_message):
        """
        Convert normalized event template into the
        Event ID used during model training.
        """

        event_id = self.event_mapping.get(
            normalized_message
        )

        if event_id is None:
            return None

        # Mapping may contain E38, E12, etc.
        # Convert it to numeric 38, 12, etc.
        if isinstance(event_id, str):

            match = re.fullmatch(
                r"E(\d+)",
                event_id
            )

            if match:
                return int(match.group(1))

        # If mapping already contains integers
        if isinstance(event_id, int):
            return event_id

        return None

    # -----------------------------------------------------
    # Parse HDFS line
    # -----------------------------------------------------

    def parse_line(self, line):
        """
        Parse one replayed HDFS log line.

        Returns:
            Dictionary containing BlockId, normalized
            message, and numeric EventId.
        """

        line = line.strip()

        if not line:
            return None

        parts = line.split()

        if len(parts) < 6:
            return None

        # ---------------------------------------------
        # Basic fields
        # ---------------------------------------------

        date = parts[0]
        time = parts[1]
        pid = parts[2]
        level = parts[3]
        component = parts[4].rstrip(":")
        message = " ".join(parts[5:])

        # ---------------------------------------------
        # Extract BlockId
        # ---------------------------------------------

        block_match = re.search(
            r"(blk_-?\d+)",
            line
        )

        block_id = (
            block_match.group(1)
            if block_match
            else None
        )

        # ---------------------------------------------
        # Normalize message
        # ---------------------------------------------

        normalized_message = (
            self.normalize_message(message)
        )

        # ---------------------------------------------
        # Find numeric Event ID
        # ---------------------------------------------

        event_id = self.get_event_id(
            normalized_message
        )

        return {
            "Date": date,
            "Time": time,
            "PID": pid,
            "Level": level,
            "Component": component,
            "Message": message,
            "NormalizedMessage": normalized_message,
            "BlockId": block_id,
            "EventId": event_id
        }


# ---------------------------------------------------------
# Main test
# ---------------------------------------------------------

if __name__ == "__main__":

    processor = ReplayProcessor()

    test_line = (
        "260817 120000 143 INFO "
        "dfs.DataNode$DataXceiver: "
        "Receiving block blk_-1608999687919862906 "
        "src: /10.250.19.102:54106 "
        "dest: /10.250.19.102:50010"
    )

    result = processor.parse_line(test_line)

    print("\nParsed Result:")

    for key, value in result.items():
        print(f"{key}: {value}")