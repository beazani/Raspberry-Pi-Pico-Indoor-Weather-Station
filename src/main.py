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
from comfort_HVAC import ComfortML
from hvac_led_manager import HVAC_LEDManager
from user_registry import get_user, register_user


import config

SCENARIO_NAME = "undefined"
TEST_START_TIME = None

def test_ml_predictions(duration_seconds=None, scenario_name="normal", payload_mode="normal", hvac = False, age=None, sex=None):
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
    
    print(f"Scenario: {scenario_name}")
    if duration_seconds:
        print(f"Duration: {duration_seconds} seconds")
    # Simple test loop
    reading_count = 0
    msg_id = 0

    start_time = time.time()
    try:
        while True:
            # Read sensor
            if duration_seconds  is not None:
                elapsed = time.time() - start_time
                if elapsed >= duration_seconds:
                    print(f"\nScenario '{scenario_name}': Duration of {duration_seconds} seconds reached, ending test.")
                    break
            temp, pres = sensor.read()
            
            if temp > 25:
                led.set_mode("ALERT")
            elif temp < 18:
                led.set_mode("UNCOMFORTABLE")
            else:
                led.set_mode("COMFORTABLE")

            if hvac:
                hvac_led = HVAC_LEDManager()
                model = ComfortML()

                print("\nComfort prediction running")
                
                label, confidence = model.predict(age, sex, temp)

                if label == 1:
                    hvac_led.set_mode_hvac("COMFORTABLE")
                    print(f"{temp}°C → Comfortable (p={confidence:.2f})")
                else:
                    hvac_led.set_mode_hvac("UNCOMFORTABLE")
                    print(f"{temp}°C → Uncomfortable (p={confidence:.2f})")

            if temp is not None:
                reading_count += 1
                
                # Add to ML
                ml.add_reading(temp)
                
                # NEW
                msg_id += 1
                payload = {
                    "id": msg_id,
                    "temperature": temp,
                    "timestamp": time.time(),
                    "scenario": scenario_name
                }

                if payload_mode == "large":
                    pred_5min = ml.predict_next(minutes_ahead=5)
                    payload["confidence"] = pred_5min["confidence"]
                    payload["change_per_sec"] = pred_5min["change_per_sec"]
                    payload["change_per_min"] = pred_5min["change_per_min"]
                    payload["change_per_hour"] = pred_5min["change_per_hour"]
                    payload["data_points"] = pred_5min["data_points"]
                    payload["prediction_id"] = pred_5min["prediction_id"]


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
        if hvac:
            hvac_led.set_mode_hvac("OFF")
        led.solid_off()
        print("\n\nTest stopped by user")
    except Exception as e:
        if hvac:
            hvac_led.set_mode_hvac("OFF")
        led.solid_off()
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
    print("4. Evaluation Scenario: Small/Large payload")
    print("5. Thermal Comfort prediction model (Age + Sex + Temperature)")

    choice = input("Enter 1, 2, 3, 4 or 5: ").strip()
    
    if choice == "1":
        config.PUBLISH_INTERVAL = 5  # normal interval
        test_ml_predictions(scenario_name="normal")
    elif choice == "2":
        quick_ml_test()
    elif choice == "3":
        print("\nSTARTING EVALUATION SCENARIOS - Low/High Number of Messages")

        # LOW N_Messages
        config.PUBLISH_INTERVAL = 10
        test_ml_predictions(
            duration_seconds=5 * 60,
            scenario_name="low_n_messages"
        )

        time.sleep(5)  # short pause between scenarios

        # HIGH N_Messages
        config.PUBLISH_INTERVAL = 2
        test_ml_predictions(
            duration_seconds=5 * 60,
            scenario_name="high_n_messages"
        )

        time.sleep(5)

        # NORMAL mode
        print("\nSwitching to normal operation")
        config.PUBLISH_INTERVAL = 5
        test_ml_predictions(scenario_name="normal")
    elif choice == "4":
        # SAME message rate for fairness
        config.PUBLISH_INTERVAL = 5

        # SMALL PAYLOAD
        test_ml_predictions(
            duration_seconds=5 * 60,
            scenario_name="small_payload",
            payload_mode="small"
        )

        time.sleep(5)

        # LARGE PAYLOAD
        test_ml_predictions(
            duration_seconds=5 * 60,
            scenario_name="large_payload",
            payload_mode="large"
        )

        time.sleep(5)

        # NORMAL MODE
        print("\nSwitching to normal operation")
        test_ml_predictions(
            scenario_name="normal",
            payload_mode="normal"
        )
    elif choice == "5":
        username = input("Enter your username: ").strip().lower()
        user = get_user(username)
        if user:
            print(f"Welcome back, {username}!")
            age_class = user["age"]
            sex = user["sex"]
        else:
            print("User not found. Registering new user.")
            age = int(input("Enter your age: "))
            if age < 30:
                age_class = 0
            elif age < 45:
                age_class = 1
            elif age < 60:
                age_class = 2
            else:
                age_class = 3
            sex_input = input("Enter sex (Male/Female): ").strip().lower()
            sex = 1 if sex_input == "male" else 0

            register_user(username, age_class, sex)
            print("User registered successfully.")
        
        test_ml_predictions(scenario_name="normal", hvac = True, age=age_class, sex=sex)
    else:
        print("Invalid choice")