import time
from machine import Pin

# try importing mqtt client
try:
    from umqtt.robust import MQTTClient
    print("✅ Imported umqtt.robust")
except ImportError:
    try:
        # from lib folder
        import sys
        sys.path.append('/lib')
        from umqtt.robust import MQTTClient
        print("Imported from /lib")
    except ImportError as e:
        print(f"cannot import MQTTClient: {e}")
        print("Install: import mip; mip.install('umqtt.robust')")
        MQTTClient = None


class MQTTManager:
    def __init__(self, broker, port, username, password, client_id):
        # initialize mqtt client
        # take details from config.py
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id
        
        # status LED
        self.status_led = Pin("LED", Pin.OUT)
        
        # create MQTT client
        self.client = MQTTClient(
            client_id=client_id,
            server=broker,
            port=port,
            user=username,
            password=password,
            ssl=True,
            keepalive=60
        )
        
        # set callback for incoming messages
        self.client.set_callback(self.on_message)
        
        # message buffer
        self.last_message = None
        
        print(f"MQTT Manager initialized for {broker}")
    
    def connect(self):
        # connect to broker
        try:
            print(f"Connecting to MQTT broker: {self.broker}")
            
            # blink LED while connecting
            for _ in range(3):
                self.status_led.value(1)
                time.sleep(0.1)
                self.status_led.value(0)
                time.sleep(0.1)
            
            # connect
            self.client.connect()
            
            # fast blink for success connection
            for _ in range(5):
                self.status_led.value(1)
                time.sleep(0.05)
                self.status_led.value(0)
                time.sleep(0.05)
            
            print("MQTT connected successfully!")
            return True
            
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            # Slow blink for error
            for _ in range(10):
                self.status_led.value(1)
                time.sleep(0.5)
                self.status_led.value(0)
                time.sleep(0.5)
            return False
    
    def publish(self, topic, message, retain=False):
        # publish message to topic
        try:
            # convert dict to JSON string
            if isinstance(message, dict):
                import json
                message = json.dumps(message)
            
            # publish
            self.client.publish(topic.encode(), str(message).encode(), retain=retain)
            
            # quick LED blink on publish
            self.status_led.value(1)
            time.sleep(0.05)
            self.status_led.value(0)
            
            print(f"Published to {topic}: {message}")
            return True
            
        except Exception as e:
            print(f"Publish failed: {e}")
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
        # decode bytes to string
        topic = topic.decode() if isinstance(topic, bytes) else topic
        message = message.decode() if isinstance(message, bytes) else message
        
        print(f"message received: {topic} -> {message}")
        self.last_message = (topic, message)
        
        # blink LED twice for received message
        for _ in range(2):
            self.status_led.value(1)
            time.sleep(0.1)
            self.status_led.value(0)
            time.sleep(0.1)
    
    def check_messages(self):
        # check for incoming messages
        try:
            self.client.check_msg()
        except Exception as e:
            print(f"Error checking messages: {e}")
    
    def disconnect(self):
        # disconnect from broker
        try:
            self.client.disconnect()
            self.status_led.value(0)
            print("MQTT disconnected")
        except:
            pass


def test_mqtt():
    # test MQTT connection
    try:
        import config
        
        print("\n" + "="*50)
        print("TESTING MQTT CONNECTION")
        print("="*50)
        
        mqtt = MQTTManager(
            config.MQTT_BROKER,
            config.MQTT_PORT,
            config.MQTT_USERNAME,
            config.MQTT_PASSWORD,
            config.MQTT_CLIENT_ID + "_test"
        )
        
        if mqtt.connect():
            # subscribe to control topic
            mqtt.subscribe(config.TOPIC_CONTROL)
            
            # publish test messages
            print("\nPublishing test messages...")
            
            # individual topics
            mqtt.publish(config.TOPIC_TEMPERATURE, "23.5")
            mqtt.publish(config.TOPIC_PRESSURE, "1013.2")
            
            data = {
                "temperature": 23.5,
                "pressure": 1013.2,
                "sensor": "BMP280",
                "test": True
            }
            mqtt.publish(config.TOPIC_ALL_DATA, data)
            
            # check for messages for 5 seconds
            print("\nChecking for messages (5 seconds)...")
            start = time.time()
            while time.time() - start < 5:
                mqtt.check_messages()
                time.sleep(0.1)
            
            # cleanup
            mqtt.disconnect()
            print("\nMQTT test complete!")
            return True
        else:
            print("\nMQTT test failed")
            return False
            
    except ImportError:
        print("config.py not found")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_mqtt()