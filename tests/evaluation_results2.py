import os
import sys
import json
import matplotlib.pyplot as plt
from influxdb_client import InfluxDBClient
from datetime import datetime, timedelta

# -----------------------------
# Configuration
# -----------------------------
INFLUX_URL = "http://localhost:8086"
INFLUX_ORG = "InternetOfThings"
INFLUX_BUCKET = "Iot_project"

INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
if not INFLUX_TOKEN:
    print("Missing INFLUX_TOKEN environment variable")
    sys.exit(1)

# -----------------------------
# Connect to InfluxDB
# -----------------------------
client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

# -----------------------------
# Helper functions
# -----------------------------
def query_all_data():
    """Query all data from the last hour"""
    flux = f'''
    from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -3h)
        |> filter(fn: (r) => r._measurement == "weather")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "temperature", "latency_ms", "id", "scenario"])
    '''
    
    tables = query_api.query(flux)
    
    all_records = []
    for table in tables:
        for record in table.records:
            data_point = {
                'time': record.values.get('_time'),
                'temperature': record.values.get('temperature'),
                'latency_ms': record.values.get('latency_ms'),
                'id': record.values.get('id'),
                'scenario': record.values.get('scenario', 'unknown')
            }
            all_records.append(data_point)
    
    return all_records

def group_by_scenario(records):
    """Group records by scenario"""
    grouped = {}
    
    for record in records:
        scenario = record['scenario']
        if scenario not in grouped:
            grouped[scenario] = []
        grouped[scenario].append(record)
    
    return grouped

def extract_field(records, field):
    """Extract a specific field from records"""
    return [r[field] for r in records if r.get(field) is not None]

def save_json(data, filename):
    """Save data to JSON file"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✓ Saved {filename}")

def plot(data, title, ylabel, filename):
    """Create and save plot"""
    if not data:
        print(f"⚠ No data to plot for {filename}")
        return
        
    plt.figure(figsize=(10, 6))
    
    for scenario, values in data.items():
        if values:
            plt.plot(values, label=scenario, marker='o', markersize=4, alpha=0.7)
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel("Sample Number", fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"✓ Saved {filename}")

# -----------------------------
# Metric computation helpers
# -----------------------------
def compute_throughput(records, publish_interval):
    """Calculate messages per minute"""
    if not records:
        return 0
    minutes = len(records) * publish_interval / 60
    return len(records) / minutes if minutes > 0 else 0

def compute_reliability(ids):
    """Calculate message delivery reliability"""
    if not ids or len(ids) < 2:
        return 100.0
    
    # Remove None values
    ids = [i for i in ids if i is not None]
    if not ids:
        return 0.0
    
    expected = max(ids) - min(ids) + 1
    actual = len(ids)
    return (actual / expected * 100) if expected > 0 else 100.0

def compute_avg_latency(latencies):
    """Calculate average latency"""
    latencies = [l for l in latencies if l is not None]
    return sum(latencies) / len(latencies) if latencies else 0

# -----------------------------
# Evaluation runner
# -----------------------------
def run_evaluation(name, scenarios, publish_intervals, grouped_data):
    """Run evaluation for a set of scenarios"""
    print(f"\n{'='*70}")
    print(f"Running evaluation: {name.replace('_', ' ').upper()}")
    print(f"{'='*70}")

    eval_latency = {}
    eval_throughput = {}
    eval_reliability = {}
    eval_summary = {}

    for scenario in scenarios:
        print(f"\n📊 Processing scenario: {scenario}")
        
        if scenario not in grouped_data:
            print(f"  ⚠ No data found for scenario '{scenario}'")
            continue
        
        records = grouped_data[scenario]
        print(f"  📝 Total records: {len(records)}")
        
        # Extract fields
        latencies = extract_field(records, 'latency_ms')
        temperatures = extract_field(records, 'temperature')
        ids = extract_field(records, 'id')
        
        # Latency
        if latencies:
            eval_latency[scenario] = latencies
            avg_lat = compute_avg_latency(latencies)
            print(f"  ⏱ Latency: avg={avg_lat:.2f}ms, samples={len(latencies)}")
        
        # Throughput
        if records:
            throughput = compute_throughput(records, publish_intervals[scenario])
            eval_throughput[scenario] = [throughput]
            print(f"  📈 Throughput: {throughput:.2f} msg/min")
        
        # Reliability
        if ids:
            reliability = compute_reliability(ids)
            eval_reliability[scenario] = [reliability]
            print(f"  ✅ Reliability: {reliability:.2f}% ({len(ids)} messages)")
        
        # Summary stats
        eval_summary[scenario] = {
            "total_messages": len(records),
            "avg_latency_ms": compute_avg_latency(latencies),
            "throughput_msg_min": compute_throughput(records, publish_intervals[scenario]),
            "reliability_percent": compute_reliability(ids)
        }

    if not eval_latency and not eval_throughput and not eval_reliability:
        print(f"\n⚠ No data found for {name} - skipping")
        return

    # Save results
    results = {
        "latency_ms": eval_latency,
        "throughput_msg_min": eval_throughput,
        "reliability_percent": eval_reliability,
        "summary": eval_summary
    }
    save_json(results, f"{name}_results.json")

    # Create plots
    if eval_latency:
        plot(eval_latency, f"{name.replace('_', ' ').title()} – Latency", 
             "Latency (ms)", f"{name}_latency.png")
    
    if eval_throughput:
        # Convert to plottable format
        throughput_plot = {k: v for k, v in eval_throughput.items()}
        plot(throughput_plot, f"{name.replace('_', ' ').title()} – Throughput", 
             "Messages / min", f"{name}_throughput.png")
    
    if eval_reliability:
        # Convert to plottable format
        reliability_plot = {k: v for k, v in eval_reliability.items()}
        plot(reliability_plot, f"{name.replace('_', ' ').title()} – Reliability", 
             "Reliability (%)", f"{name}_reliability.png")

# -----------------------------
# Main execution
# -----------------------------
print("\n" + "="*70)
print("📊 IoT PROJECT EVALUATION - DATA ANALYSIS")
print("="*70)

# Query all data
print("\n🔍 Querying InfluxDB...")
all_records = query_all_data()

if not all_records:
    print("❌ No data found in InfluxDB for the last hour!")
    print("\nTroubleshooting:")
    print("1. Make sure you've run the Pico tests (main.py)")
    print("2. Check that Node-RED is running and connected to InfluxDB")
    print("3. Verify InfluxDB is running: http://localhost:8086")
    sys.exit(1)

print(f"✓ Found {len(all_records)} total records")

# Group by scenario
grouped_data = group_by_scenario(all_records)

print(f"\n📁 Found {len(grouped_data)} scenarios:")
for scenario, records in grouped_data.items():
    print(f"  • {scenario}: {len(records)} records")

# Define publish intervals for each scenario
MESSAGE_INTERVALS = {
    "low_n_messages": 10,
    "high_n_messages": 2,
    "normal": 5
}

PAYLOAD_INTERVALS = {
    "small_payload": 5,
    "large_payload": 5,
    "normal": 5
}

# Run evaluations
if any(s in grouped_data for s in ["low_n_messages", "high_n_messages"]):
    run_evaluation(
        name="message_rate_evaluation",
        scenarios=["low_n_messages", "high_n_messages"],
        publish_intervals=MESSAGE_INTERVALS,
        grouped_data=grouped_data
    )

if any(s in grouped_data for s in ["small_payload", "large_payload"]):
    run_evaluation(
        name="payload_size_evaluation",
        scenarios=["small_payload", "large_payload"],
        publish_intervals=PAYLOAD_INTERVALS,
        grouped_data=grouped_data
    )

print("\n" + "="*70)
print("✅ EVALUATION COMPLETED")
print("="*70)
print("\nGenerated files:")
print("  • *_results.json - Raw data and metrics")
print("  • *_latency.png - Latency comparison plots")
print("  • *_throughput.png - Throughput comparison plots")
print("  • *_reliability.png - Reliability comparison plots")
print("="*70 + "\n")