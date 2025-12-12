import time
from machine import Pin
import ssl

try:
    from umqtt.robust import MQTTClient
    print("Imported umqtt.robust")
except ImportError:
    try:
        import sys
        sys.path.append('/lib')
        from umqtt.robust import MQTTClient
        print("Imported from /lib")
    except ImportError as e:
        print(f"cannot import MQTTClient: {e}")
        print("Install: import mip; mip.install('umqtt.robust')")
        MQTTClient = None

class MQTTManager:
    # initialize MQTT manager
    def __init__(self, broker, port, username, password, client_id):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id
        
        self.led_manager = None
        
        ssl_params = {'server_hostname': broker} if ssl else None
        
        self.client = MQTTClient(
            client_id=client_id,
            server=broker,
            port=port,
            user=username,
            password=password,
            ssl=True,
            ssl_params=ssl_params,
            keepalive=60
        )
        
        self.client.set_callback(self.on_message)
        
        self.last_message = None
        
        print(f"MQTT Manager initialized for {broker}")
    
    def connect(self):
        # connect to MQTT broker
        try:
            print(f"Connecting to MQTT broker: {self.broker}")
            
            if self.led_manager:
                self.led_manager.set_mode("MQTT_CONNECTING")
            
            self.client.connect()
            
            if self.led_manager:
                self.led_manager.set_mode("MQTT_CONNECTED", duration_ms=2000)
            
            print("MQTT connected successfully!")
            return True
            
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            
            if self.led_manager:
                self.led_manager.set_mode("ERROR", duration_ms=3000)
            
            return False
    
    def publish(self, topic, message, retain=False):
        # publish message to topic
        try:
            if isinstance(message, dict):
                import json
                message = json.dumps(message)
            
            self.client.publish(topic.encode(), str(message).encode(), retain=retain)
            
            if self.led_manager:
                self.led_manager.set_mode("DATA_SENT", duration_ms=300)
            
            print(f"Published to {topic}: {message}")
            return True
            
        except Exception as e:
            print(f"Publish failed: {e}")
            
            if self.led_manager:
                self.led_manager.set_mode("ERROR", duration_ms=1000)
            
            return False
    
    def subscribe(self, topic):
        # subscribe to topic
        try:
            self.client.subscribe(topic.encode())
            print(f"Subscribed to {topic}")
            return True
        except Exception as e:
            print(f"Subscribe failed: {e}")
            return False
    
    def on_message(self, topic, message):
        # handle incoming messages
        topic = topic.decode() if isinstance(topic, bytes) else topic
        message = message.decode() if isinstance(message, bytes) else message
        
        print(f"Control message received: {topic} -> {message}")
        
        if topic.endswith("control"):
            #print(f"LED Command: {message}")
            
            if self.led_manager:
                if message in ["ALERT", "UNCOMFORTABLE", "COMFORTABLE"]:
                    self.led_manager.set_mode(message, duration_ms=5000)
                    print(f"   LED set to: {message} pattern")
                elif message == "ON":
                    self.led_manager.solid_on()
                    print("   LED turned ON")
                elif message == "OFF":
                    self.led_manager.solid_off()
                    print("   LED turned OFF")
                elif message == "BLINK":
                    self.led_manager.pulse(3, 0.2)
                    print("   LED blinking")
                else:
                    print(f"   Unknown LED command: {message}")
            else:
                print("   Warning: LED Manager not available")
        
        self.last_message = (topic, message)
        
        if self.led_manager:
            self.led_manager.pulse(2, 0.1)
    
    def check_messages(self):
        try:
            self.client.check_msg()
        except Exception as e:
            print(f"Error checking messages: {e}")
            
            if self.led_manager:
                self.led_manager.set_mode("ERROR", duration_ms=500)
    
    def disconnect(self):
        try:
            self.client.disconnect()
            
            if self.led_manager:
                self.led_manager.solid_off()
            
            print("MQTT disconnected")
        except:
            pass

def test_mqtt_with_led_manager():
    try:
        import config
        from led_manager import LEDManager
        
        print("TESTING MQTT WITH LED MANAGER ONLY")

        
        print("\n1. Initializing LED Manager...")
        led = LEDManager(config.LED_PIN)
        led.set_status_patterns(config.LED_STATUS)
        print("LED Manager ready")
        
        print("\n2. Initializing MQTT Manager...")
        mqtt = MQTTManager(
            config.MQTT_BROKER,
            config.MQTT_PORT,
            config.MQTT_USERNAME,
            config.MQTT_PASSWORD,
            config.MQTT_CLIENT_ID + "-test-" + str(time.time_ns())[-6:]
        )
        
        mqtt.led_manager = led
        print("LED Manager connected to MQTT")
        
        if mqtt.connect():
            mqtt.subscribe(config.TOPIC_CONTROL)
            
            print("\n3. Testing publishing with LED feedback...")
            mqtt.publish(config.TOPIC_TEMPERATURE, "23.5")
            mqtt.publish(config.TOPIC_PRESSURE, "1013.2")
            
            print("\n4. Testing LED control patterns...")
            
            print("\n5. Waiting for control messages (30 seconds)...")
            start = time.time()
            while time.time() - start < 30:
                mqtt.check_messages()
                time.sleep(0.1)
            
            mqtt.disconnect()
            print("\nTest complete!")
            return True
        else:
            print("\nMQTT connection failed")
            return False
            
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def simple_mqtt_test():
    try:
        import config
        
        print("SIMPLE MQTT TEST")
        
        mqtt = MQTTManager(
            config.MQTT_BROKER,
            config.MQTT_PORT,
            config.MQTT_USERNAME,
            config.MQTT_PASSWORD,
            config.MQTT_CLIENT_ID
        )
        
        if mqtt.connect():
            print("\nPublishing test messages...")
            
            mqtt.publish(config.TOPIC_TEMPERATURE, "23.5")
            mqtt.publish(config.TOPIC_PRESSURE, "1013.2")
            
            data = {
                "temperature": 23.5,
                "pressure": 1013.2,
                "sensor": "BMP280",
                "test": True
            }
            mqtt.publish(config.TOPIC_ALL_DATA, data)
            
            mqtt.disconnect()
            print("\nSimple test complete!")
            return True
        else:
            print("\nSimple test failed")
            return False
            
    except ImportError:
        print("config.py not found")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if not test_mqtt_with_led_manager():
        print("Falling back to simple test...")
        simple_mqtt_test()