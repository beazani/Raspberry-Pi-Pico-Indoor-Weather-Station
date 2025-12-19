import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/sensor_data.dart';

class SensorChart extends StatelessWidget {
  final SensorData data;
  final Color color;
  
  const SensorChart({
    Key? key,
    required this.data,
    required this.color,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    if (data.values.isEmpty) {
      return const Center(child: Text('No hay datos'));
    }
    
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              data.label,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 15),
            SizedBox(
              height: 200,
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: data.label.contains('Air Density') ? 0.01 : null,  // ← NUEVO
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: Colors.grey.shade300,
                      strokeWidth: 1,
                    ),
                  ),
                  titlesData: FlTitlesData(
                    show: true,
                    rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        interval: (data.values.length / 4).ceilToDouble(),
                        getTitlesWidget: (value, meta) {
                          if (value.toInt() >= data.timestamps.length) return const Text('');
                          return Text(
                            data.timestamps[value.toInt()],
                            style: const TextStyle(fontSize: 9),
                          );
                        },
                      ),
                    ),
                    leftTitles: AxisTitles(//modify
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,  // ← Aumentar espacio para decimales
                        getTitlesWidget: (value, meta) {
                          // Si es Air Density, mostrar 2 decimales
                          if (data.label.contains('Air Density')) {
                            return Text(
                              value.toStringAsFixed(4),  // ← 2 decimales
                              style: const TextStyle(fontSize: 9),
                            );
                          }
                          // Para otros gráficos, sin decimales
                          return Text(
                            value.toStringAsFixed(0),
                            style: const TextStyle(fontSize: 10),
                          );
                        },
                      ),
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  minX: 0,
                  maxX: (data.values.length - 1).toDouble(),
                  minY: data.label.contains('Air Density') ? 1.16 : data.minValue - 2, //min of value "y" in Air Density
                  maxY: data.label.contains('Air Density') ? 1.19 : data.maxValue + 2, //max of value "y" in Air Density
                  lineBarsData: [
                    LineChartBarData(
                      spots: List.generate(
                        data.values.length,
                        (i) => FlSpot(i.toDouble(), data.values[i]),
                      ),
                      isCurved: true,
                      color: color,
                      barWidth: 2,
                      dotData: FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        color: color.withOpacity(0.2),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}