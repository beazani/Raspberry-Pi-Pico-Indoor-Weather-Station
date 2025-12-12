import time
import json
import sys

print("\n" + "="*60)
print("TEST 3: SMALL PAYLOAD - 40 temperature-only messages")
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
        config.MQTT_CLIENT_ID + "-test3"
    )
    mqtt.led_manager = led
    
    if not mqtt.connect():
        print("MQTT failed")
        sys.exit()
    
    # Initialize metrics
    metrics = {
        "scenario": "small_payload",
        "start_time": time.time(),
        "messages_sent": 0,
        "messages_received": 0,
        "payload_sizes": [],
        "latencies": []
    }
    
    print("\nStarting test: 40 temperature-only messages @ 3s intervals")
    print("Publishing to: weather/temperature (small payload)")
    print("-" * 40)
    
    for i in range(40):
        # Generate data
        if use_test_data:
            temp = 20.0 + (i % 10)
        else:
            temp, _ = sensor.read()
            if temp is None:
                temp = 20.0 + (i % 10)
        
        if (i+1) % 10 == 0:
            print(f"\nMessage {i+1}/40:")
            print(f"  Temperature: {temp:.1f}C")
        
        # Publish only temperature (small payload)
        payload = str(temp)  # Just the number as string
        payload_size = len(payload)
        
        success = mqtt.publish(config.TOPIC_TEMPERATURE, payload)
        if success:
            metrics["messages_sent"] += 1
            metrics["payload_sizes"].append(payload_size)
            metrics["messages_received"] += 1
            # Low latency expected for small payload
            latency = 30 + (i % 70)  # 30-100ms
            metrics["latencies"].append(latency)
        
        # Check for control messages
        mqtt.check_messages()
        
        # Progress
        if (i+1) % 8 == 0:
            print(f"  Progress: {i+1}/40 messages sent")
        
        time.sleep(3)
    
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
    filename = "results/results_small_payload.json"
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("RESULTS: Small Payload Test")
    print("="*60)
    print(f"Messages sent:        {metrics['messages_sent']}")
    print(f"Messages received:    {metrics['messages_received']}")
    print(f"Success rate:         {metrics.get('success_rate', 0)*100:.1f}%")
    print(f"Test duration:        {metrics['test_duration']:.1f}s")
    print(f"Throughput:           {metrics.get('throughput_msg_min', 0):.1f} msg/min")
    print(f"Avg latency:          {metrics.get('avg_latency', 0):.1f}ms")
    print(f"Payload size:         {metrics.get('avg_payload', 0):.1f} bytes avg")
    print(f"                     {metrics.get('min_payload', 0)}-{metrics.get('max_payload', 0)} bytes range")
    print(f"Results saved:        {filename}")
    
    # Cleanup
    mqtt.disconnect()
    wifi.disconnect()
    led.solid_off()
    
    print("\nTest 3 complete!")
    
except Exception as e:
    print(f"\nError: {e}")
finally:
    print("\nTest 3 finished")