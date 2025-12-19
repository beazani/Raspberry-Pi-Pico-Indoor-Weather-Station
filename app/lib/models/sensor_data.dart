class SensorData {
  final List<String> timestamps;
  final List<double> values;
  final String label;
  
  SensorData({
    required this.timestamps,
    required this.values,
    required this.label,
  });
  
  factory SensorData.fromJson(Map<String, dynamic> json, String label) {
    return SensorData(
      timestamps: List<String>.from(json['x']),
      values: List<double>.from(json['y'].map((e) => e is int ? e.toDouble() : e)),
      label: label,
    );
  }
  
  double get currentValue => values.isNotEmpty ? values.last : 0.0;
  double get maxValue => values.isNotEmpty ? values.reduce((a, b) => a > b ? a : b) : 0.0;
  double get minValue => values.isNotEmpty ? values.reduce((a, b) => a < b ? a : b) : 0.0;
}