import time
import machine
import sys

print("\n" + "="*60)
print("IoT WEATHER STATION - BMP280")
print("="*60)

class WeatherStation:
    def __init__(self):
        # initialize all components needed
        print("\nInitializing Weather Station...")
        
        # try to import all components
        try:
            from wifi_manager import WiFiManager
            from sensor_manager import WeatherSensor
            from mqtt_client import MQTTManager
            from ml_processor import EdgeMLProcessor
            from security import SimpleSecurity
            import config
            
            self.config = config
            self.components_loaded = True
            print("All components imported")
            
        except ImportError as e:
            print(f"Missing component: {e}")
            self.components_loaded = False
            return
        
        # initialize components
        print("\n1. Initializing LED...")
        try:
            from led_manager import LEDManager
            self.led = LEDManager(self.config.LED_PIN)
            self.led.set_status_patterns(self.config.LED_STATUS)
            print("LED initialized")
        except Exception as e:
            print(f"LED failed: {e}")
            self.led = None
        
        print("\n2. Initializing Wi-Fi...")
        self.wifi = WiFiManager(
            self.config.WIFI_SSID,
            self.config.WIFI_PASSWORD,
            self.led
        )
        
        print("\n3. Initializing Sensor (BMP280)...")
        self.sensor = WeatherSensor(sda_pin=20, scl_pin=21)
        
        print("\n4. Initializing MQTT...")
        self.mqtt = MQTTManager(
            self.config.MQTT_BROKER,
            self.config.MQTT_PORT,
            self.config.MQTT_USERNAME,
            self.config.MQTT_PASSWORD,
            self.config.MQTT_CLIENT_ID
        )
        
        print("\n5. Initializing ML Processor...")
        self.ml = EdgeMLProcessor()
        
        print("\n6. Initializing Security...")
        self.security = SimpleSecurity(key=0xAB)
        
        print("\nAll components initialized!")
        
        # statistics initialization
        self.reading_count = 0
        self.error_count = 0
        self.start_time = time.time()
    
    def connect_all(self):
        # connect to wifi and mqtt
        print("\n" + "="*40)
        print("CONNECTING TO NETWORK")
        print("="*40)
        
        # connect to Wi-Fi
        if not self.wifi.connect(timeout=self.config.WIFI_TIMEOUT):
            print("Wi-Fi failed, retrying in 10 seconds...")
            time.sleep(10)
            return False
        
        # connect to MQTT
        if not self.mqtt.connect():
            print("MQTT failed, retrying in 10 seconds...")
            time.sleep(10)
            return False
        
        # subscribe to control topic
        self.mqtt.subscribe(self.config.TOPIC_CONTROL)
        
        print("\nNetwork connected!")
        return True
    
    def read_and_publish(self):
        # read sensor and publish data
        self.reading_count += 1
        
        print(f"\nReading #{self.reading_count}")
        print("-" * 30)
        
        # LED: sensor reading
        if self.led:
            self.led.set_mode("SENSOR_READING", duration_ms=500)
        
        # read sensor
        temperature, pressure = self.sensor.read()
        
        if temperature is None:
            print("Sensor read failed")
            self.error_count += 1
            return False
        
        print(f"Temperature: {temperature}°C")
        print(f"Pressure: {pressure}hPa")
        
        # ML Prediction --> to add after adding functionality
        # ml_result = self.ml.predict_comfort(temperature)
        # print(f"ML: {ml_result['status']} ({ml_result['score']}/100)")
        
        # prepare data
        sensor_data = {
            "temperature": temperature,
            "pressure": pressure,
            # "comfort_score": ml_result["score"],
            # "comfort_status": ml_result["status"],
            "reading": self.reading_count,
            "errors": self.error_count,
            "sensor": "BMP280",
            "timestamp": time.time()
        }
        
        # publish to individual topics
        print("\nPublishing data...")
        
        # individual values
        self.mqtt.publish(self.config.TOPIC_TEMPERATURE, temperature)
        self.mqtt.publish(self.config.TOPIC_PRESSURE, pressure)
        # self.mqtt.publish(self.config.TOPIC_COMFORT, ml_result["status"])
        
        # complete JSON data
        self.mqtt.publish(self.config.TOPIC_ALL_DATA, sensor_data)
        
        # encrypted data (security demonstration)
        encrypted = self.security.encrypt_sensor_data(temperature, pressure)
        self.mqtt.publish(self.config.TOPIC_SECURE, encrypted)
        
        # status metrics
        uptime = time.time() - self.start_time
        metrics = {
            "readings": self.reading_count,
            "errors": self.error_count,
            "uptime": round(uptime, 1),
            "free_memory": machine.mem_free()
        }
        self.mqtt.publish(self.config.TOPIC_METRICS, metrics)
        
        # LED: data sent
        if self.led:
            self.led.set_mode("DATA_SENT", duration_ms=300)
        
        print("Data published successfully!")
        return True
    
    def check_control_messages(self):
        # check for control messages
        try:
            self.mqtt.check_messages()
            
            if self.mqtt.last_message:
                topic, message = self.mqtt.last_message
                print(f"\nControl message: {topic} -> {message}")
                
                # handle control commands
                if topic.endswith("control"):
                    if message.lower() == "on" or message == "1":
                        print("   Turning LED ON")
                        if self.led:
                            self.led.solid_on()
                    elif message.lower() == "off" or message == "0":
                        print("   Turning LED OFF")
                        if self.led:
                            self.led.solid_off()
                    elif message.lower() == "blink":
                        print("   LED blink")
                        if self.led:
                            self.led.pulse(3, 0.2)
                
                # clear last message
                self.mqtt.last_message = None
                
        except Exception as e:
            print(f"Control check error: {e}")
    
    def run(self):
        """Main loop"""
        # main loop
        if not self.components_loaded:
            print("Cannot start - components missing")
            return
        
        print("\n" + "="*60)
        print("STARTING WEATHER STATION")
        print("="*60)
        
        # connect to network
        while not self.connect_all():
            print("Retrying connection...")
            time.sleep(5)
        
        # main loop
        print("\n" + "="*60)
        print("RUNNING - Press Ctrl+C to stop")
        print("="*60)
        
        try:
            while True:
                # read and publish
                success = self.read_and_publish()
                
                # check for control messages
                self.check_control_messages()
                
                # wait for next reading
                print(f"\nWaiting {self.config.PUBLISH_INTERVAL} seconds...")
                for i in range(self.config.PUBLISH_INTERVAL * 2):
                    self.check_control_messages()
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            print("\n\nStopping...")
        except Exception as e:
            print(f"\nError in main loop: {e}")
        finally:
            # cleanup
            print("\nCleaning up...")
            self.mqtt.disconnect()
            self.wifi.disconnect()
            if self.led:
                self.led.solid_off()
            
            # statistics
            uptime = time.time() - self.start_time
            print(f"\nStatistics:")
            print(f"   Total readings: {self.reading_count}")
            print(f"   Errors: {self.error_count}")
            print(f"   Uptime: {uptime:.1f} seconds")
            print(f"   Success rate: {100 * (1 - self.error_count/max(self.reading_count, 1)):.1f}%")
            
            print("\nWeather Station stopped")

# run the application
if __name__ == "__main__":
    station = WeatherStation()
    station.run()