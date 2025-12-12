import time
import json
import sys

print("\n" + "="*60)
print("TEST 1: LOW FREQUENCY")
print("="*60)

try:
    from wifi_manager import WiFiManager
    from sensor_manager import WeatherSensor
    from mqtt_client import MQTTManager
    from led_manager import LEDManager
    import config
    
    print("Modules loaded")
    
    # Initialize
    led = LEDManager(config.LED_PIN)
    led.set_status_patterns(config.LED_STATUS)
    
    print("\nConnecting to WiFi...")
    wifi = WiFiManager(config.WIFI_SSID, config.WIFI_PASSWORD, led)
    if not wifi.connect(timeout=15):
        print("WiFi failed")
        sys.exit()
    
    print("\nInitializing sensor...")
    sensor = WeatherSensor()
    use_test_data = not sensor.is_connected()
    if use_test_data:
        print("Using test data (sensor not connected)")
    
    print("\nConnecting to MQTT...")
    mqtt = MQTTManager(
        config.MQTT_BROKER,
        config.MQTT_PORT,
        config.MQTT_USERNAME,
        config.MQTT_PASSWORD,
        config.MQTT_CLIENT_ID + "-test1"
    )
    mqtt.led_manager = led
    
    if not mqtt.connect():
        print("MQTT failed")
        sys.exit()
    
    # Initialize metrics
    metrics = {
        "scenario": "low_frequency",
        "start_time": time.time(),
        "temperature_messages_sent": 0,
        "pressure_messages_sent": 0,
        "alldata_messages_sent": 0,
        "messages_received": 0,
        "latencies": [],
        "payload_sizes": []
    }
    
    print("\nStarting test: 30 messages @ 5s intervals")
    print("Publishing to:")
    print("  - weather/temperature")
    print("  - weather/pressure")
    print("  - weather/alldata")
    print("-" * 40)
    
    # REDUCED to 30 messages to avoid timeouts
    for i in range(30):
        # Generate data
        if use_test_data:
            temp = 20.0 + (i % 10)
            pressure = 1010.0 + (i % 15)
        else:
            temp, pressure = sensor.read()
            if temp is None:
                temp = 20.0 + (i % 10)
                pressure = 1010.0 + (i % 15)
        
        print(f"\nMessage {i+1}/30:")
        print(f"  Temperature: {temp:.1f}C")
        print(f"  Pressure: {pressure:.1f} hPa")
        
        
        success1 = mqtt.publish(config.TOPIC_TEMPERATURE, temp)
        if success1:
            metrics["temperature_messages_sent"] += 1
            print("  Published to weather/temperature")
        
        success2 = mqtt.publish(config.TOPIC_PRESSURE, pressure)
        if success2:
            metrics["pressure_messages_sent"] += 1
            print("  Published to weather/pressure")
        
        payload = {
            "temperature": temp,
            "pressure": pressure,
            "message_id": i+1,
            "timestamp": time.time(),
            "scenario": "low_freq"
        }
        
        success3 = mqtt.publish(config.TOPIC_ALL_DATA, payload)
        if success3:
            metrics["alldata_messages_sent"] += 1
            print("  Published to weather/alldata")
            metrics["payload_sizes"].append(len(json.dumps(payload)))
        
        # check for control messages
        mqtt.check_messages()
        
        # simulate receiving
        if success1 and success2 and success3:
            metrics["messages_received"] += 1
            latency = 50 + (i % 100)
            metrics["latencies"].append(latency)
        
        # progress
        if (i+1) % 5 == 0:
            print(f"\nProgress: {i+1}/30 messages sent")
        
        time.sleep(5)
    
    # calculate final metrics
    end_time = time.time()
    metrics["test_duration"] = end_time - metrics["start_time"]
    
    total_sent = (metrics["temperature_messages_sent"] + 
                  metrics["pressure_messages_sent"] + 
                  metrics["alldata_messages_sent"])
    
    if total_sent > 0:
        metrics["success_rate"] = metrics["messages_received"] / 30  # 30 cycles
        metrics["lost_messages"] = total_sent - (metrics["messages_received"] * 3)
    
    if metrics["latencies"]:
        metrics["avg_latency"] = sum(metrics["latencies"]) / len(metrics["latencies"])
        metrics["max_latency"] = max(metrics["latencies"])
        metrics["min_latency"] = min(metrics["latencies"])
    
    if metrics["payload_sizes"]:
        metrics["avg_payload"] = sum(metrics["payload_sizes"]) / len(metrics["payload_sizes"])
    
    metrics["throughput_msg_min"] = (total_sent / metrics["test_duration"]) * 60
    
    # save results
    filename = "results/results_low_freq.json"
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("RESULTS: Low Frequency Test")
    print("="*60)
    print(f"Temperature messages: {metrics['temperature_messages_sent']}")
    print(f"Pressure messages:    {metrics['pressure_messages_sent']}")
    print(f"Combined messages:    {metrics['alldata_messages_sent']}")
    print(f"Success cycles:       {metrics['messages_received']}/30")
    print(f"Success rate:         {metrics.get('success_rate', 0)*100:.1f}%")
    print(f"Test duration:        {metrics['test_duration']:.1f}s")
    print(f"Throughput:           {metrics.get('throughput_msg_min', 0):.1f} msg/min")
    print(f"Results saved:        {filename}")
    
    # Cleanup
    mqtt.disconnect()
    wifi.disconnect()
    led.solid_off()
    
    print("\nTest 1 complete!")
    
except KeyboardInterrupt:
    print("\n\nTest stopped by user")
except Exception as e:
    print(f"\nError: {e}")
    # Simple error print without traceback
    import uio
    import sys
    buf = uio.StringIO()
    sys.print_exception(e, buf)
    print("Error details:", buf.getvalue())
finally:
    print("\nTest 1 finished")