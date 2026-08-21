import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import numpy as np
from tensorflow.keras.models import load_model


class LSTMPredictor:

    def __init__(
        self,
        model_path="models/LSTM_model.keras",
        threshold=0.5
    ):
        self.model = load_model(model_path)
        self.threshold = threshold

        print("LSTM model loaded successfully.")
        print("Model input shape:", self.model.input_shape)
        print("Model output shape:", self.model.output_shape)

    def predict(self, sequence):
        """
        Predict Normal (0) or Anomaly (1)
        for a single event sequence.

        Short sequences are post-padded to 298,
        matching the training preprocessing.
        """

        if len(sequence) == 0:
            raise ValueError("Sequence cannot be empty.")

        # Keep only the latest 298 events
        sequence = sequence[-298:]

        # Post-padding with 0
        padded_sequence = sequence + [0] * (298 - len(sequence))

        X = np.array(
            padded_sequence,
            dtype=np.int32
        ).reshape(1, 298)

        probability = float(
            self.model.predict(
                X,
                verbose=0
            )[0][0]
        )

        prediction = (
            1
            if probability >= self.threshold
            else 0
        )

        return {
            "prediction": prediction,
            "label": (
                "Anomaly"
                if prediction == 1
                else "Normal"
            ),
            "probability": probability
        }

    
if __name__ == "__main__":

    predictor = LSTMPredictor()

    test_sequence = [38, 12, 34, 36, 11] * 60
    test_sequence = test_sequence[:298]

    result = predictor.predict(
        test_sequence
    )

    print("\nPrediction Result:")
    print(result)