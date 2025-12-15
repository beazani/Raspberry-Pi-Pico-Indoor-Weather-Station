"""
TEST CODE FOR YOUR WORKING ML PREDICTOR
Just tests the ML predictions with MQTT
"""

import ntptime
import time
import machine
from wifi_manager import WiFiManager
from mqtt_client import MQTTManager
from sensor_manager import WeatherSensor
from ml_predictor import MLPredictor  # Your working predictor
from led_manager import LEDManager  # New LED manager

import config



def test_ml_predictions():
    print("=" * 60)
    print("TEST: ML PREDICTIONS TO MQTT")
    print("=" * 60)
    led = LEDManager()
    led.set_status_patterns(config.LED_PATTERNS)

    # 1. Connect to Wi-Fi
    print("\n[1/3] Connecting to Wi-Fi...")
    led.set_mode("WIFI_CONNECTING")
    wifi = WiFiManager(config.WIFI_SSID, config.WIFI_PASSWORD)
    if not wifi.connect(timeout=config.WIFI_TIMEOUT):
        print("Wi-Fi failed")
        led.set_mode("WIFI_ERROR")
        return
    
    led.set_mode("WIFI_CONNECTED")

    # Synchronize time via NTP
    try:
        print("Syncing time via NTP...")
        ntptime.host = "pool.ntp.org"  # default NTP server
        ntptime.settime()  # sets Pico RTC
        print("Time synchronized")
    except Exception as e:
        print("NTP sync failed:", e)


    # 2. Connect to MQTT
    print("[2/3] Connecting to MQTT...")
    mqtt = MQTTManager(
        config.MQTT_BROKER,
        config.MQTT_PORT,
        config.MQTT_USERNAME,
        config.MQTT_PASSWORD,
        "pico-ml-test"
    )
    
    if not mqtt.connect():
        print("MQTT failed")
        wifi.disconnect()
        return
    
    # 3. Initialize sensor
    print("[3/3] Initializing sensor...")
    sensor = WeatherSensor()
    if not sensor.is_connected():
        print("Sensor not found")
        mqtt.disconnect()
        wifi.disconnect()
        return
    
    # 4. Initialize ML (YOUR WORKING PREDICTOR)
    print("\nInitializing YOUR ML predictor...")
    ml = MLPredictor(reading_interval=config.PUBLISH_INTERVAL)
    
    # Ready
    print("\nREADY!")
    print("Will publish ML predictions to:")
    print("  - weather/predictions/5min")
    print("  - weather/predictions/15min")
    print("  - weather/predictions/30min")
    print("\nStarting in 2 seconds...")
    time.sleep(2)
    
    # Simple test loop
    reading_count = 0
    msg_id = 0

    try:
        while True:
            # Read sensor
            temp, pres = sensor.read()
            
            if temp > 25:
                led.set_mode("ALERT")
            elif temp < 18:
                led.set_mode("UNCOMFORTABLE")
            else:
                led.set_mode("COMFORTABLE")

            if temp is not None:
                reading_count += 1
                
                # Add to ML
                ml.add_reading(temp)
                
                # NEW
                msg_id += 1
                payload = {
                    "id": msg_id,
                    "temperature": temp,
                    "timestamp": time.time()
                }

                mqtt.publish(config.TOPIC_TEMPERATURE, payload)
                #mqtt.publish(config.TOPIC_TEMPERATURE, temp)
                mqtt.publish(config.TOPIC_PRESSURE, pres)
                
                # Make ML prediction every 30 seconds (or 6 readings at 5s interval)
                if reading_count % 6 == 0:  # Every 6 readings = 30 seconds
                    print("\n" + "─" * 40)
                    print(f"ML PREDICTION #{reading_count//6}")
                    print("─" * 40)
                    
                    # Create predictions for different timeframes
                    predictions = []
                    
                    # 5-minute prediction
                    pred_5min = ml.predict_next(minutes_ahead=5)
                    pred_5min["timeframe"] = "5min"
                    predictions.append(("5min", pred_5min))
                    
                    # 15-minute prediction  
                    pred_15min = ml.predict_next(minutes_ahead=15)
                    pred_15min["timeframe"] = "15min"
                    predictions.append(("15min", pred_15min))
                    
                    # 30-minute prediction
                    pred_30min = ml.predict_next(minutes_ahead=30)
                    pred_30min["timeframe"] = "30min"
                    predictions.append(("30min", pred_30min))
                    
                    # Publish all predictions
                    for timeframe, prediction in predictions:
                        topic = f"weather/predictions/{timeframe}"
                        success = mqtt.publish(topic, prediction)
                        
                        if success:
                            print(f"{timeframe}: {prediction['predicted']}°C")
                        else:
                            print(f"Failed to publish {timeframe}")
                    
                    # Show details for 5-minute prediction
                    print(f"\nCurrent: {pred_5min['current']}°C")
                    print(f"Predicted (5min): {pred_5min['predicted']}°C")
                    print(f"Trend: {pred_5min['trend']}")
                    print(f"Confidence: {pred_5min['confidence']*100:.0f}%")
                
                # Simple status every 10 readings
                if reading_count % 10 == 0:
                    print(f"\nStatus: {reading_count} readings processed")
            
            # Check for MQTT messages
            mqtt.check_messages()
            
            # Wait
            time.sleep(config.PUBLISH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
    except Exception as e:
        print(f"\n\nError: {e}")
    finally:
        print("\nCleaning up...")
        mqtt.disconnect()
        wifi.disconnect()
        print("Test complete!")


# Quick standalone test without Wi-Fi/MQTT
def quick_ml_test():
    """Test ML predictor alone"""
    print("\n" + "=" * 60)
    print("QUICK ML TEST (No Wi-Fi/MQTT)")
    print("=" * 60)
    
    # Create ML predictor
    ml = MLPredictor(reading_interval=5)
    
    # Test with sample temperatures
    test_temps = [19.0, 19.1, 19.2, 19.3, 19.4, 19.5, 19.6]
    
    print("\nTesting with temperatures:", test_temps)
    print("-" * 40)
    
    for i, temp in enumerate(test_temps):
        ml.add_reading(temp)
        
        if i >= 1:  # Start predicting after 2 readings
            prediction = ml.predict_next(minutes_ahead=5)
            
            print(f"\nReading {i+1}: {temp}°C")
            print(f"  Current: {prediction['current']}°C")
            print(f"  Predicted (5min): {prediction['predicted']}°C")
            print(f"  Trend: {prediction['trend']}")
            print(f"  Confidence: {prediction['confidence']*100:.0f}%")
    
    print("\nQuick test complete!")


# Run what you need
if __name__ == "__main__":
    print("Choose test:")
    print("1. Full test with Wi-Fi/MQTT")
    print("2. Quick ML test only")
    print("3. Evaluation Scenario: Small/Large n° of messages")
    
    choice = input("Enter 1, 2 or 3: ").strip()
    
    if choice == "1":
        test_ml_predictions()
    elif choice == "2":
        quick_ml_test()
    elif choice == "3":
        # Ask for scenario type
        scenario = input("Choose scenario: 1=low load, 2=high load: ").strip()
        if scenario == "1":
            config.PUBLISH_INTERVAL = 10  # low load
            print("Running low-load scenario (1 message every 10s)...")
        elif scenario == "2":
            config.PUBLISH_INTERVAL = 1   # high load
            print("Running high-load scenario (1 message every 1s)...")
        else:
            print("Invalid scenario choice, defaulting to low load")
            config.PUBLISH_INTERVAL = 10
        
        test_ml_predictions()