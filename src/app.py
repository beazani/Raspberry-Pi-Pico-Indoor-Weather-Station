from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient
from influxdb_client.client.flux_table import FluxTable
from flask_cors import CORS
import os
import sys

app = Flask(__name__)
CORS(app)

# InfluxDB Configuration
INFLUX_URL = "http://localhost:8086"
ORG = "InternetOfThings"
BUCKET = "Iot_project"

INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
if not INFLUX_TOKEN:
    print("Missing INFLUX_TOKEN")
    sys.exit(1)

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG)
query_api = client.query_api()

def query_influx(flux_query):
    """Executes a Flux query and returns x (time) and y (values)"""
    tables = query_api.query(flux_query)
    xvalues = []
    yvalues = []

    for table in tables:
        for record in table.records:
            xvalues.append(record.get_time().strftime("%H:%M:%S"))
            try:
                yvalues.append(record.get_value())
            except:
                yvalues.append(None)
    return xvalues, yvalues

# Temperature endpoint
@app.route('/temperature', methods=['GET'])
def temperature():
    flux_query = f'''
    from(bucket:"{BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "weather" and r._field == "temperature")
    '''
    x, y = query_influx(flux_query)
    return jsonify({"x": x, "y": y})


# Pressure endpoint
@app.route('/pressure', methods=['GET'])
def pressure():
    flux_query = f'''
    from(bucket:"{BUCKET}")
      |> range(start: -6h)
      |> filter(fn: (r) => r._measurement == "weather" and r._field == "pressure")
    '''
    x, y = query_influx(flux_query)
    return jsonify({"x": x, "y": y})

# Air density trend endpoint
@app.route('/air_density', methods=['GET'])
def air_density():
    R = 287.05  # specific gas constant
    flux_query = f'''
    temperature = from(bucket:"{BUCKET}")
      |> range(start: -6h)
      |> filter(fn: (r) => r._measurement == "weather" and r._field == "temperature")
      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")

    pressure = from(bucket:"{BUCKET}")
      |> range(start: -6h)
      |> filter(fn: (r) => r._measurement == "weather" and r._field == "pressure")
      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")

    join(tables: {{T: temperature, P: pressure}}, on: ["_time"])
      |> map(fn: (r) => ({{_time: r._time, _value: r.pressure / ( {R} * (r.temperature + 273.15) ), _field: "Air density trend"}}))
    '''
    x, y = query_influx(flux_query)
    return jsonify({"x": x, "y": y})

# Temperature alerts endpoint
@app.route('/temperature_alerts', methods=['GET'])
def temperature_alerts():
    flux_query = f'''
    from(bucket:"{BUCKET}")
      |> range(start: -6h)
      |> filter(fn: (r) => r._measurement == "temperature_alerts" and r._field == "status")
      |> sort(columns: ["_time"], desc: true)
    '''
    x, y = query_influx(flux_query)
    return jsonify({"x": x, "y": y})

# ML Predictions and current temperature endpoint
@app.route('/ml_predictions', methods=['GET'])
def ml_predictions():
    flux_query = f'''
    predictions =
    from(bucket:"{BUCKET}")
      |> range(start: -6h)
      |> filter(fn: (r) => r._measurement == "ml_predictions")
      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> filter(fn: (r) => r.timeframe_min == 5 or r.timeframe_min == 15 or r.timeframe_min == 30)
      |> keep(columns: ["_time", "predicted_temp", "timeframe_min"])
      |> map(fn: (r) => ({{_time: r._time, _value: r.predicted_temp, series: if r.timeframe_min == 5 then "Prediction (5 min)" else if r.timeframe_min == 15 then "Prediction (15 min)" else "Prediction (30 min)"}}))
      |> group(columns: ["series"])

    current =
    from(bucket:"{BUCKET}")
      |> range(start: -30m)
      |> filter(fn: (r) => r._measurement == "ml_predictions")
      |> filter(fn: (r) => r._field == "current_temp")
      |> map(fn: (r) => ({{_time: r._time, _value: r._value, series: "Current temperature"}}))
      |> group(columns: ["series"])

    union(tables: [predictions, current])
    '''
    x, y = query_influx(flux_query)
    return jsonify({"x": x, "y": y})

# Latency endpoint
@app.route('/latency', methods=['GET'])
def latency():
    flux_query = f'''
    from(bucket:"{BUCKET}")
      |> range(start: -6h)
      |> filter(fn: (r) => r._field == "latency_ms")
    '''
    x, y = query_influx(flux_query)
    return jsonify({"x": x, "y": y})

# Temperature count per minute endpoint
@app.route('/temperature_count', methods=['GET'])
def temperature_count():
    flux_query = f'''
    from(bucket:"{BUCKET}")
      |> range(start: -6h)
      |> filter(fn: (r) => r._measurement == "weather" and r._field == "temperature")
      |> aggregateWindow(every: 1m, fn: count)
    '''
    x, y = query_influx(flux_query)
    return jsonify({"x": x, "y": y})

# Root route
@app.route('/')
def home():
    return "Flask API running. Endpoints: /temperature, /pressure, /air_density, /temperature_alerts, /ml_predictions, /latency, /temperature_count"

# Run server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)