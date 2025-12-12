import time

class MLPredictor:
    # initialize ML predictor
    
    def __init__(self, window_size=5, reading_interval=5):
        # window_size: number of readings to consider for prediction
        self.history = []
        self.window_size = window_size
        self.reading_interval = reading_interval
        self.prediction_count = 0
        
        print(f"SimpleMLPredictor ready (interval: {reading_interval}s)")
    
    def add_reading(self, temperature):
        # add new temperature reading
        # if window becomes too large, remove oldest data value
        self.history.append(round(temperature, 1))
        
        if len(self.history) > self.window_size:
            self.history.pop(0)
    
    def predict_next(self, minutes_ahead=5):
        self.prediction_count += 1
        
        # if not enough data --> return current reading as prediction
        if len(self.history) < 2:
            current = self.history[-1] if self.history else 0
            return {
                'current': current,
                'predicted': current,
                'trend': 'no_data',
                'confidence': 0.1,
                'prediction_id': self.prediction_count
            }
        
        current_temp = self.history[-1]
        
        # calculate trend
        if len(self.history) >= 2:
            # get last change in temperature
            temp_change = self.history[-1] - self.history[0]
            # number of intervals between readings
            time_span = len(self.history) - 1
            
            if time_span > 0:
                # change per reading
                change_per_reading = temp_change / time_span
                
                # convert to change per second
                change_per_second = change_per_reading / self.reading_interval
                
                # predict: current + (change_per_second * seconds_ahead)
                seconds_ahead = minutes_ahead * 60
                predicted_change = change_per_second * seconds_ahead
                
                # max 3 C change limnit
                max_change = 3.0
                if predicted_change > max_change:
                    predicted_change = max_change
                elif predicted_change < -max_change:
                    predicted_change = -max_change
                
                predicted_temp = current_temp + predicted_change
                
                # determine trend
                # if change per reading > 0.01 C, rising; < -0.01 C, falling; else stable
                if change_per_reading > 0.01:
                    trend = 'rising'
                elif change_per_reading < -0.01:
                    trend = 'falling'
                else:
                    trend = 'stable'
                
                # calculate confidence as function of data points
                # max 90% confidence
                # more data points = higher confidence
                confidence = min(0.9, len(self.history) / self.window_size * 0.8)
                
                # calculate change per hour for display
                change_per_hour = change_per_second * 3600
                
            else:
                predicted_temp = current_temp
                trend = 'stable'
                confidence = 0.5
                change_per_hour = 0
        else:
            predicted_temp = current_temp
            trend = 'stable'
            confidence = 0.3
            change_per_hour = 0
        
        predicted_temp = max(0, min(40, predicted_temp))
        
        return {
            'current': current_temp,
            'predicted': round(predicted_temp, 1),
            'trend': trend,
            'confidence': round(confidence, 2),
            'change_per_hour': round(change_per_hour, 2),
            'prediction_id': self.prediction_count,
            'data_points': len(self.history),
            'timestamp': time.time()
        }