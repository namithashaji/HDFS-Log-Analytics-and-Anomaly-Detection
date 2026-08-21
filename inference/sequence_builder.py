from collections import defaultdict, deque


class SequenceBuilder:

    def __init__(self, max_length=298):
        """
        Maintain a fixed-size event window for each HDFS BlockId.
        """

        self.max_length = max_length

        self.sequences = defaultdict(
            lambda: deque(maxlen=self.max_length)
        )

    def add_event(self, parsed_event):
        """
        Add one event to the sequence belonging to its BlockId.

        The sequence automatically keeps only the latest
        max_length events.
        """

        if parsed_event is None:
            return None

        block_id = parsed_event.get("BlockId")
        event_id = parsed_event.get("EventId")

        if block_id is None or event_id is None:
            return None

        self.sequences[block_id].append(event_id)

        return list(self.sequences[block_id])

    def get_sequence(self, block_id):
        """
        Return the current sequence for a BlockId.
        """

        return list(
            self.sequences.get(block_id, [])
        )

    def get_all_sequences(self):
        """
        Return all currently maintained sequences.
        """

        return {
            block_id: list(sequence)
            for block_id, sequence
            in self.sequences.items()
        }

    def sequence_length(self, block_id):
        """
        Return the current sequence length.
        """

        return len(
            self.sequences.get(block_id, [])
        )

    def is_ready(self, block_id):
        """
        Check whether the sequence has reached
        the LSTM's expected input length.
        """

        return (
            self.sequence_length(block_id)
            >= self.max_length
        )

    def clear_sequence(self, block_id):
        """
        Remove the sequence for a BlockId.
        """

        self.sequences.pop(
            block_id,
            None
        )

if __name__ == "__main__":

    builder = SequenceBuilder(max_length=298)

    for event_id in range(1, 301):
        builder.add_event({
            "BlockId": "test_block",
            "EventId": event_id
        })

    sequence = builder.get_sequence("test_block")

    print("Sequence length:", len(sequence))
    print("First 10:", sequence[:10])
    print("Last 10:", sequence[-10:])