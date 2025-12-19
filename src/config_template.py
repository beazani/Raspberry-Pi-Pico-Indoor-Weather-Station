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
LED_PATTERNS = {
    # Wi-Fi states
    "WIFI_CONNECTING": (0.2, 0.2),   # fast blink
    "WIFI_CONNECTED": (0.05, 1.0),   # heartbeat
    "WIFI_ERROR": (0.3, 0.3),        # slow blink

    # Alerts
    "COMFORTABLE": (0.05, 0.95),     # calm pulse
    "UNCOMFORTABLE": (0.15, 0.15),   # noticeable blink
    "ALERT": (0.05, 0.05),           # rapid blink
}

# Sensor configuration
SENSOR_I2C_CHANNEL = 0
SENSOR_SCL_PIN = 20
SENSOR_SDA_PIN = 21

# System configuration
PUBLISH_INTERVAL = 5      # Seconds between readings
ML_UPDATE_INTERVAL = 60   # Seconds between ML status updates
WIFI_TIMEOUT = 20         # Seconds to wait for Wi-Fi connection
MQTT_TIMEOUT = 10         # Seconds to wait for MQTT connection