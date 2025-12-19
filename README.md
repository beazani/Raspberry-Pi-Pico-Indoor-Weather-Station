# IoT Thermal Comfort Monitoring System

This repository contains an end-to-end **IoT-based thermal comfort monitoring system** built around a **Raspberry Pi Pico W** and a **BMP280 sensor** for temperature and pressure acquisition.  
The system collects environmental data, streams it through a cloud-based pipeline, performs comfort prediction using a machine learning model, and visualizes results in real time across dashboards and a mobile application.

---

## Quick Start

Connect the Raspberry Pi Pico W. From VisualStudioCode with MicroPico extension:

```
MicroPico: Connect
MicroPico: Upload project to Pico
MicroPico: Run current file on Pico    # While having src/main.py open
```

Config:

A config.py file has to be created, by filling the missing values in the config_template.py file. Raspberry Pi Pico W has to be connected to a private network with known name and password access.

For influx-db:

```bash
# Move to the path where influxdb is stored
./influxd
```

For node-red:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
Node-RED
```

Main running:

```bash
python src/main.py
```

---

## Project Structure

Below is the high-level folder structure of the repository:

```
├── app/                    # Flutter mobile APP folder 
│ 
├── HVAC/
│ ├── dataset_creation.py
│ └── train_model.py
│
├── src/
│ ├── app.py                # Flask REST API
│ ├── bmp280.py
│ ├── comfort_HVAC.py
│ ├── config_template.py    # Create your config.py
│ ├── hvac_led_manager.py
│ ├── led_manager.py
│ ├── main.py
│ ├── ml_predictor.py
│ ├── mqtt_client.py
│ ├── nodered_flow.json
│ ├── sensor_manager.py
│ ├── user_registry.py
│ └── wifi_manager.py
│
├── tests/                  # Evaluation plots
│
├── requirements.txt
└── README.md
```

---

## System Overview

The project integrates **hardware, networking, data engineering, machine learning, and visualization** into a single pipeline:

1. **Data Acquisition**
   - Raspberry Pi Pico W
   - BMP280 temperature & pressure sensor

2. **Connectivity**
   - WiFi-enabled communication
   - MQTT protocol
   - HiveMQ as the MQTT broker

3. **Data Processing & Storage**
   - Node-RED for data routing
   - InfluxDB for time-series data storage

4. **Visualization & Alerts**
   - Grafana dashboards
   - Automated email alerts triggered by threshold conditions

5. **Mobile Application**
   - Flutter-based mobile app
   - REST API built with Flask for data access

6. **Real-Time Comfort Feedback**
   - Prediction based on a **Logistic Regression model**
   - Model trained on the **ASHRAE Global Thermal Comfort Dataset**
   - Predictions based on **temperature, user age and sex**
   - Red LED and Green LED to visualize it in real-time

---

## Hardware Components

- Raspberry Pi Pico W
- BMP280 temperature & pressure sensor
- Breadboard
- 2 LEDs (Green / Red)
- 2 120ohm resistors (current limiting)
- Jumper wires

---
