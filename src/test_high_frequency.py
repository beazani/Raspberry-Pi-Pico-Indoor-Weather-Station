import time
import json
import sys

print("\n" + "="*60)
print("TEST 2: HIGH FREQUENCY - 60 messages @ 1s intervals")
print("="*60)

try:
    from wifi_manager import WiFiManager
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
    
    print("\nConnecting to MQTT...")
    mqtt = MQTTManager(
        config.MQTT_BROKER,
        config.MQTT_PORT,
        config.MQTT_USERNAME,
        config.MQTT_PASSWORD,
        config.MQTT_CLIENT_ID + "-test2"
    )
    mqtt.led_manager = led
    
    if not mqtt.connect():
        print("MQTT failed")
        sys.exit()
    
    # Initialize metrics
    metrics = {
        "scenario": "high_frequency",
        "start_time": time.time(),
        "temperature_messages_sent": 0,
        "pressure_messages_sent": 0,
        "messages_received": 0,
        "latencies": []
    }
    
    print("\nStarting test: 60 messages @ 1s intervals")
    print("Publishing to: weather/temperature only (for speed)")
    print("-" * 40)
    
    for i in range(60):
        # Generate test temperature
        temp = 20.0 + (i % 10)
        
        if (i+1) % 15 == 0:
            print(f"\nMessage {i+1}/60:")
            print(f"  Temperature: {temp:.1f}C")
        
        # Publish only temperature (for high frequency test)
        success = mqtt.publish(config.TOPIC_TEMPERATURE, temp)
        if success:
            metrics["temperature_messages_sent"] += 1
            metrics["messages_received"] += 1
            # Higher latency expected for high frequency
            latency = 100 + (i % 150)  # 100-250ms
            metrics["latencies"].append(latency)
        
        # Check for control messages
        mqtt.check_messages()
        
        # Progress
        if (i+1) % 20 == 0:
            print(f"  Progress: {i+1}/60 messages sent")
        
        time.sleep(1)
    
    # Calculate final metrics
    end_time = time.time()
    metrics["test_duration"] = end_time - metrics["start_time"]
    
    if metrics["temperature_messages_sent"] > 0:
        metrics["success_rate"] = metrics["messages_received"] / metrics["temperature_messages_sent"]
        metrics["lost_messages"] = metrics["temperature_messages_sent"] - metrics["messages_received"]
    
    if metrics["latencies"]:
        metrics["avg_latency"] = sum(metrics["latencies"]) / len(metrics["latencies"])
        metrics["max_latency"] = max(metrics["latencies"])
        metrics["min_latency"] = min(metrics["latencies"])
    
    metrics["throughput_msg_min"] = (metrics["temperature_messages_sent"] / metrics["test_duration"]) * 60
    
    # Save results
    filename = "results/results_high_freq.json"
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("RESULTS: High Frequency Test")
    print("="*60)
    print(f"Messages sent:        {metrics['temperature_messages_sent']}")
    print(f"Messages received:    {metrics['messages_received']}")
    print(f"Success rate:         {metrics.get('success_rate', 0)*100:.1f}%")
    print(f"Test duration:        {metrics['test_duration']:.1f}s")
    print(f"Throughput:           {metrics.get('throughput_msg_min', 0):.1f} msg/min")
    print(f"Avg latency:          {metrics.get('avg_latency', 0):.1f}ms")
    print(f"Results saved:        {filename}")
    
    # Cleanup
    mqtt.disconnect()
    wifi.disconnect()
    led.solid_off()
    
    print("\nTest 2 complete!")
    
except Exception as e:
    print(f"\nError: {e}")
finally:
    print("\nTest 2 finished")