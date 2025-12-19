import time
from machine import Pin, Timer

class LEDManager:
    """Manages single LED blinking patterns for status indication."""
    def __init__(self, led_pin="LED"):
        # Initialize LED on specified pin
        self.led = Pin(led_pin, Pin.OUT)
        self.current_mode = None
        self.timer = Timer()
        self.blink_active = False
        self.led_state = 0
        
        # default LED states from config
        self.status_patterns = {}
        
        print("LED Manager initialized (single LED mode)")
    
    def set_status_patterns(self, patterns):
        """Set the blinking patterns dictionary for different status modes."""
        self.status_patterns = patterns
    
    def set_mode(self, mode_name, duration_ms=None):
        """Set LED mode with pattern priority handling for alerts vs data patterns."""
        if mode_name not in self.status_patterns:
            print(f"LED mode '{mode_name}' not found. Available: {list(self.status_patterns.keys())}")
            return False
    
        # check if this is an alert/temperature pattern that should override others
        alert_patterns = ["COMFORTABLE", "UNCOMFORTABLE", "ALERT", "ERROR"]
        data_patterns = ["DATA_SENT", "SENSOR_READING"]
    
        current_is_alert = self.current_mode in alert_patterns
        new_is_alert = mode_name in alert_patterns
        current_is_data = self.current_mode in data_patterns
    
        # if an alert is already shown, don't interrupt with data patterns
        if current_is_alert and mode_name in data_patterns:
            return False
    
        # if we have a data pattern showing and get an alert, stop the data pattern
        if current_is_data and new_is_alert:
            print(f"Stopping data pattern {self.current_mode} for alert {mode_name}")
            self.stop_blink()
    
        # check if we want extended duration
        extended = mode_name in alert_patterns
    
        # get timing values
        on_time, off_time = self.status_patterns[mode_name]
    
        # apply extension for alert patterns
        if extended:
            EXTENSION_FACTOR = 5  # 5x longer for alerts
            on_time = on_time * EXTENSION_FACTOR
            off_time = off_time * EXTENSION_FACTOR
        else:
            pass
    
        # Calculate timing
        period_ms = int((on_time + off_time) * 1000)
        duty_cycle = on_time / (on_time + off_time)
    
        # Start blinking
        self.start_blink(period_ms, duty_cycle, duration_ms)
    
        # Update current mode
        self.current_mode = mode_name
    
        return True
    
    def start_blink(self, period_ms, duty_cycle, duration_ms=None):
        """Start blinking with specified period, duty cycle, and optional duration."""
        if self.blink_active:
            self.stop_blink()
        
        on_time_ms = int(period_ms * duty_cycle)
        
        self.timer.init(
            period=period_ms,
            mode=Timer.PERIODIC,
            callback=lambda t: self._toggle_led(on_time_ms)
        )
        
        self.blink_active = True
        
        if duration_ms:
            Timer(-1).init(
                mode=Timer.ONE_SHOT,
                period=duration_ms,
                callback=lambda t: self.stop_blink()
            )
    
    def _toggle_led(self, on_time_ms):
        """Internal method to toggle LED state during blinking."""
        if self.led_state == 0:
            # turn LED on
            self.led.value(1)
            self.led_state = 1
            # schedule turn off
            Timer(-1).init(
                mode=Timer.ONE_SHOT,
                period=on_time_ms,
                callback=lambda t: self.led.off() or setattr(self, 'led_state', 0)
            )
        else:
            # turn LED off
            self.led.value(0)
            self.led_state = 0
    
    def stop_blink(self):
        """Stop blinking and turn LED off."""
        if hasattr(self, 'timer'):
            try:
                self.timer.deinit()
            except:
                pass
        
        self.led.value(0)
        self.led_state = 0
        self.blink_active = False
        self.current_mode = None
    
    def solid_on(self):
        """Turn LED solid on."""
        self.stop_blink()
        self.led.value(1)
        self.current_mode = "SOLID_ON"
    
    def solid_off(self):
        """Turn LED solid off."""
        self.stop_blink()
        self.led.value(0)
        self.current_mode = "SOLID_OFF"
    
    def pulse(self, count=1, pulse_duration=0.1):
        """Pulse the LED a specified number of times."""
        self.stop_blink()
        
        for i in range(count):
            self.led.value(1)
            time.sleep(pulse_duration)
            self.led.value(0)
            if i < count - 1:
                time.sleep(pulse_duration)
        
        self.current_mode = f"PULSE_{count}"
    
    def indicate_error(self, error_code):
        """Indicate error code with blinking pattern (number of blinks per digit)."""
        self.stop_blink()
        
        for digit in str(error_code):
            if digit.isdigit():
                num = int(digit)
                # blink for the number
                for _ in range(num):
                    self.led.value(1)
                    time.sleep(0.2)
                    self.led.value(0)
                    time.sleep(0.2)
                time.sleep(0.5)
        
        print(f"LED Error indication: {error_code}")
    
    def get_status(self):
        """Return current LED status including mode, state, and blinking status."""
        return {
            "mode": self.current_mode,
            "state": "ON" if self.led_state else "OFF",
            "blinking": self.blink_active
        }


def test_led_manager():
    """Test all LED patterns and functions."""
    print("Testing LED Manager...")
    
    # Test patterns
    test_patterns = {
        "CONNECTING": (0.2, 0.2),
        "CONNECTED": (0.05, 0.95),
        "ACTIVE": (0.02, 0.08),
        "ALERT": (0.05, 0.05),
    }
    
    led = LEDManager()
    led.set_status_patterns(test_patterns)
    
    print("\nTesting patterns (3 seconds each):")
    
    patterns_to_test = ["CONNECTING", "CONNECTED", "ACTIVE", "ALERT"]
    
    for pattern in patterns_to_test:
        print(f"\nPattern: {pattern}")
        led.set_mode(pattern, duration_ms=3000)
        time.sleep(3.2)
    
    print("\nTesting pulses:")
    led.pulse(3)
    time.sleep(1)
    led.pulse(5)
    
    print("\nTesting error indication:")
    led.indicate_error(404)
    
    print("\nLED test complete!")
    led.solid_off()

if __name__ == "__main__":
    test_led_manager()