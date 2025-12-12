import time
import sys

print("\n=== WEATHER STATION ===")

try:
    from wifi_manager import WiFiManager
    from sensor_manager import WeatherSensor
    from mqtt_client import MQTTManager
    from led_manager import LEDManager
    import config
    
    print("All modules loaded")
    
    led = LEDManager(config.LED_PIN)
    led.set_status_patterns(config.LED_STATUS)
    led.pulse(2, 0.1)
    
    print("\nConnecting to WiFi...")
    wifi = WiFiManager(config.WIFI_SSID, config.WIFI_PASSWORD, led)
    if wifi.connect(timeout=10):
        print(f"WiFi connected: {wifi.get_ip()}")
        led.pulse(3, 0.1)
    else:
        print("WiFi failed!")
        sys.exit()
    
    print("\nInitializing sensor...")
    sensor = WeatherSensor(sda_pin=20, scl_pin=21)
    if not sensor.is_connected():
        print("✗ Sensor failed!")
    
    print("\nConnecting to MQTT...")
    mqtt = MQTTManager(
        config.MQTT_BROKER,
        config.MQTT_PORT,
        config.MQTT_USERNAME,
        config.MQTT_PASSWORD,
        config.MQTT_CLIENT_ID
    )
    
    mqtt.led_manager = led
    
    if mqtt.connect():
        mqtt.subscribe(config.TOPIC_CONTROL)
        print("MQTT connected & subscribed to control")
        led.pulse(4, 0.1)
    else:
        print("✗ MQTT failed!")
        sys.exit()
    
    print("\n" + "="*40)
    print("SENDING DATA TO INFLUXDB & GRAFANA")
    print("="*40)
    print("Press Ctrl+C to stop\n")
    
    counter = 0
    try:
        while True:
            counter += 1
            
            if sensor and sensor.is_connected():
                temp, pressure = sensor.read()
                if temp is None:
                    temp = 22.0 + (counter % 10)
                    pressure = 1013.0 + (counter % 20)
                    print(f"⚠ Using test data")
            else:
                temp = 22.0 + (counter % 10)
                pressure = 1013.0 + (counter % 20)
                print(f"No sensor, using test data")
            
            print(f"\nReading #{counter}:")
            print(f"  Temp: {temp}°C")
            print(f"  Pressure: {pressure}hPa")
            
            led.set_mode("SENSOR_READING", duration_ms=500)
            
            mqtt.publish(config.TOPIC_TEMPERATURE, temp)
            mqtt.publish(config.TOPIC_PRESSURE, pressure)
            
            data = {
                "temperature": temp,
                "pressure": pressure,
                "reading": counter,
                "timestamp": time.time(),
                "sensor": "BMP280"
            }
            mqtt.publish(config.TOPIC_ALL_DATA, data)
            
            led.set_mode("DATA_SENT", duration_ms=300)
            
            mqtt.check_messages()
            
            time.sleep(config.PUBLISH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
except KeyboardInterrupt:
    print("\n\nStopped during setup")
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\nCleaning up...")
    try:
        mqtt.disconnect()
    except:
        pass
    try:
        wifi.disconnect()
    except:
        pass
    try:
        led.solid_off()
    except:
        pass
    print("System stopped")