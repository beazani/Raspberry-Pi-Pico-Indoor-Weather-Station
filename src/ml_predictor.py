import time

class MLPredictor:
    """
    Lightweight trend-based predictor for temperature data.
    Designed for MicroPython / Raspberry Pi Pico.
    """

    def __init__(self, window_size=50, reading_interval=5):
        self.history = []
        self.window_size = window_size
        self.reading_interval = reading_interval
        self.prediction_count = 0

        # EMA smoothing factor
        self.alpha = 0.2

        print(f"MLPredictor ready (window={window_size}, interval={reading_interval}s)")

    
    # Data ingestion
    def add_reading(self, temperature):
        """Add a temperature reading to the history buffer."""
        self.history.append(round(temperature, 1))

        if len(self.history) > self.window_size:
            self.history.pop(0)

    # Internal helpers
    def _smoothed_rate_c_per_sec(self):
        """Returns smoothed temperature change rate in °C per second using exponential moving average over per-reading deltas."""
        n = len(self.history)
        if n < 3:
            return 0.0

        # Initial rate estimate
        rate = (self.history[1] - self.history[0]) / self.reading_interval

        # EMA over deltas
        for i in range(2, n):
            delta = (self.history[i] - self.history[i - 1]) / self.reading_interval
            rate = self.alpha * delta + (1 - self.alpha) * rate

        return rate

    def _change_per_hour(self):
        """Returns bounded temperature change per hour (°C/hour)."""
        change_per_hour = self._smoothed_rate_c_per_sec() * 3600
        # Physical sanity bounds
        return max(-5.0, min(5.0, change_per_hour))

    def _change_per_min(self):
        """Return bounded temperature change per minute (°C/min)."""
        change_per_min = self._smoothed_rate_c_per_sec() * 60
        return max(-1.0, min(1.0, change_per_min))

    # Prediction API
    def predict_next(self, minutes_ahead=5):
        """Generate temperature prediction for specified minutes ahead with trend and confidence."""
        self.prediction_count += 1

        if not self.history:
            return {
                "current": 0,
                "predicted": 0,
                "trend": "no_data",
                "confidence": 0.1,
                "prediction_id": self.prediction_count
            }

        current_temp = self.history[-1]

        # Smoothed rate
        rate_per_sec = self._smoothed_rate_c_per_sec()

        # Prediction
        seconds_ahead = minutes_ahead * 60
        predicted_change = rate_per_sec * seconds_ahead

        # Limit extrapolation swing
        predicted_change = max(-3.0, min(3.0, predicted_change))
        predicted_temp = current_temp + predicted_change

        # Fix to plausible temperature range
        predicted_temp = max(0.0, min(40.0, predicted_temp))

        # Trend classification
        if rate_per_sec > 0.0005:        # °C/hour
            trend = "rising"
        elif rate_per_sec < -0.0005:     # °C/hour
            trend = "falling"
        else:
            trend = "stable"

        # Confidence estimation
        data_factor = min(1.0, len(self.history) / self.window_size)
        stability_factor = 1.0 - min(1.0, abs(self._change_per_hour()) / 5.0)

        confidence = 0.2 + 0.7 * data_factor * stability_factor
        confidence = round(confidence, 2)

        return {
            "current": round(current_temp, 1),
            "predicted": round(predicted_temp, 1),
            "trend": trend,
            "confidence": confidence,
            "change_per_sec": round(rate_per_sec, 4),
            "change_per_min": round(self._change_per_min(), 2),
            "change_per_hour": round(self._change_per_hour(), 2),
            "prediction_id": self.prediction_count,
            "data_points": len(self.history),
            "timestamp": time.time()
        }
