# configuration of wifi parameters
WIFI_SSID = ""
WIFI_PASSWORD = ""

# MQTT broker configuration
MQTT_BROKER = ""
MQTT_PORT = 8883
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = ""

# MQTT topics
TOPIC_TEMPERATURE = "weather/temperature"
TOPIC_PRESSURE = "weather/pressure"
TOPIC_ALL_DATA = "weather/alldata"
TOPIC_CONTROL = "weather/control"
TOPIC_COMFORT = "weather/comfort"
TOPIC_METRICS = "weather/metrics"
TOPIC_SECURE = "weather/secure"

# LED configuration
LED_PIN = "LED"
LED_STATUS = {
    "WIFI_CONNECTING": (0.2, 0.2),
    "WIFI_CONNECTED": (0.05, 0.95),
    "MQTT_CONNECTING": (0.1, 0.1),
    "MQTT_CONNECTED": (0.05, 0.45),
    "SENSOR_READING": (0.02, 0.08),
    "DATA_SENT": (0.01, 0.04),
    "COMFORTABLE": (0.5, 0.5),
    "UNCOMFORTABLE": (0.1, 0.1),
    "ALERT": (0.05, 0.05),
    "ERROR": (0.5, 0.1),
}

# Sensor configuration
SENSOR_I2C_CHANNEL = 0
SENSOR_SCL_PIN = 20
SENSOR_SDA_PIN = 21

# System configuration
PUBLISH_INTERVAL = 5      # seconds between readings
ML_UPDATE_INTERVAL = 60   # Seconds between ML status updates
WIFI_TIMEOUT = 20         # Seconds to wait for Wi-Fi connection
MQTT_TIMEOUT = 10         # Seconds to wait for MQTT connection

# Evaluation settings
# EVALUATION_MODE = False
# TEST_PAYLOAD_SMALL = "test_small"
# TEST_PAYLOAD_LARGE = "test_large"