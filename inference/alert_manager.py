class AlertManager:

    def __init__(self):
        # Stores the latest state of each BlockId
        self.block_states = {}

    def process_prediction(
        self,
        block_id,
        prediction_result
    ):
        """
        Decide whether a prediction should generate
        a new alert.

        Returns:
            True  -> generate alert
            False -> suppress alert
        """

        is_anomaly = (
            prediction_result["prediction"] == 1
        )

        previous_state = self.block_states.get(
            block_id,
            "Normal"
        )

        current_state = (
            "Anomaly"
            if is_anomaly
            else "Normal"
        )

        # Update state
        self.block_states[block_id] = current_state

        # Alert only when transitioning
        # from Normal -> Anomaly
        if (
            current_state == "Anomaly"
            and previous_state == "Normal"
        ):
            return True

        return False

    def reset(self, block_id):
        """
        Remove the stored state for a BlockId.
        """

        self.block_states.pop(
            block_id,
            None
        )