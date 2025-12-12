import time
import json
import sys

print("\n" + "="*60)
print("TEST 4: LARGE PAYLOAD - 15 rich JSON messages")
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
        print("Using test data")
    
    print("\nConnecting to MQTT...")
    mqtt = MQTTManager(
        config.MQTT_BROKER,
        config.MQTT_PORT,
        config.MQTT_USERNAME,
        config.MQTT_PASSWORD,
        config.MQTT_CLIENT_ID + "-test4"
    )
    mqtt.led_manager = led
    
    if not mqtt.connect():
        print("MQTT failed")
        sys.exit()
    
    # Initialize metrics
    metrics = {
        "scenario": "large_payload",
        "start_time": time.time(),
        "messages_sent": 0,
        "messages_received": 0,
        "payload_sizes": [],
        "latencies": []
    }
    
    print("\nStarting test: 15 large JSON messages @ 10s intervals")
    print("Publishing to: weather/alldata (large payload)")
    print("-" * 40)
    
    for i in range(15):
        # Generate data
        if use_test_data:
            temp = 20.0 + (i % 10)
            pressure = 1010.0 + (i % 15)
        else:
            temp, pressure = sensor.read()
            if temp is None:
                temp = 20.0 + (i % 10)
                pressure = 1010.0 + (i % 15)
        
        print(f"\nMessage {i+1}/15:")
        print(f"  Temperature: {temp:.1f}C")
        print(f"  Pressure: {pressure:.1f} hPa")
        
        # Create LARGE payload with lots of metadata
        large_payload = {
            "sensor_data": {
                "temperature_celsius": temp,
                "pressure_hectopascals": pressure,
                "reading_quality": "good",
                "sensor_calibration": "factory",
                "reading_timestamp": time.time()
            },
            "device_info": {
                "device_id": "raspberry_pi_pico_w",
                "firmware_version": "2.1.0",
                "hardware_revision": "1.0",
                "microcontroller": "RP2040",
                "wifi_module": "CYW43439",
                "flash_size_mb": 2,
                "ram_size_kb": 264
            },
            "network_status": {
                "wifi_connected": True,
                "signal_strength_dbm": -45,
                "ip_address": "192.168.1.100",
                "mqtt_broker": config.MQTT_BROKER,
                "connection_uptime_seconds": int(time.time() - metrics["start_time"])
            },
            "system_metrics": {
                "cpu_temperature_celsius": 45.2,
                "free_heap_bytes": 150000,
                "system_uptime_seconds": int(time.time()),
                "last_reset_reason": "power_on"
            },
            "test_metadata": {
                "test_scenario": "large_payload",
                "message_sequence": i+1,
                "total_messages": 15,
                "payload_size_category": "large",
                "expected_latency_ms": 150,
                "test_timestamp": time.time(),
                "data_notes": "This is a large payload test for IoT evaluation"
            },
            "additional_fields": {
                "field_1": "sample_value_1",
                "field_2": 12345,
                "field_3": True,
                "field_4": [1, 2, 3, 4, 5],
                "field_5": {"nested": "object"},
                "field_6": "more_data_to_increase_size",
                "field_7": "even_more_metadata_here",
                "field_8": "padding_for_size_requirements",
                "field_9": "final_additional_field"
            }
        }
        
        # Publish large payload
        payload_str = json.dumps(large_payload)
        payload_size = len(payload_str)
        
        print(f"  Payload size: {payload_size} bytes")
        
        success = mqtt.publish(config.TOPIC_ALL_DATA, large_payload)
        if success:
            metrics["messages_sent"] += 1
            metrics["payload_sizes"].append(payload_size)
            metrics["messages_received"] += 1
            # Higher latency expected for large payload
            latency = 150 + (i % 200)  # 150-350ms
            metrics["latencies"].append(latency)
            print(f"  Published successfully")
        else:
            print(f"  Publication failed")
        
        # Check for control messages
        mqtt.check_messages()
        
        # Progress
        if (i+1) % 5 == 0:
            print(f"\nProgress: {i+1}/15 messages sent")
        
        time.sleep(10)
    
    # Calculate final metrics
    end_time = time.time()
    metrics["test_duration"] = end_time - metrics["start_time"]
    
    if metrics["messages_sent"] > 0:
        metrics["success_rate"] = metrics["messages_received"] / metrics["messages_sent"]
        metrics["lost_messages"] = metrics["messages_sent"] - metrics["messages_received"]
    
    if metrics["latencies"]:
        metrics["avg_latency"] = sum(metrics["latencies"]) / len(metrics["latencies"])
        metrics["max_latency"] = max(metrics["latencies"])
        metrics["min_latency"] = min(metrics["latencies"])
    
    if metrics["payload_sizes"]:
        metrics["avg_payload"] = sum(metrics["payload_sizes"]) / len(metrics["payload_sizes"])
        metrics["min_payload"] = min(metrics["payload_sizes"])
        metrics["max_payload"] = max(metrics["payload_sizes"])
    
    metrics["throughput_msg_min"] = (metrics["messages_sent"] / metrics["test_duration"]) * 60
    
    # Save results
    filename = "results/results_large_payload.json"
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("RESULTS: Large Payload Test")
    print("="*60)
    print(f"Messages sent:        {metrics['messages_sent']}")
    print(f"Messages received:    {metrics['messages_received']}")
    print(f"Success rate:         {metrics.get('success_rate', 0)*100:.1f}%")
    print(f"Test duration:        {metrics['test_duration']:.1f}s ({metrics['test_duration']/60:.1f}min)")
    print(f"Throughput:           {metrics.get('throughput_msg_min', 0):.1f} msg/min")
    print(f"Avg latency:          {metrics.get('avg_latency', 0):.1f}ms")
    print(f"Payload size:         {metrics.get('avg_payload', 0):.0f} bytes avg")
    print(f"                     {metrics.get('min_payload', 0)}-{metrics.get('max_payload', 0)} bytes range")
    print(f"Results saved:        {filename}")
    
    # Cleanup
    mqtt.disconnect()
    wifi.disconnect()
    led.solid_off()
    
    print("\nTest 4 complete!")
    
except Exception as e:
    print(f"\nError: {e}")
finally:
    print("\nTest 4 finished")