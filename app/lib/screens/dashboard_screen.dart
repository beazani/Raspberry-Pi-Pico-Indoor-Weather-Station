import 'dart:async';
import 'package:flutter/material.dart';
import '../models/sensor_data.dart';
import '../services/api_service.dart';
import '../widgets/sensor_card.dart';
import '../widgets/chart_widget.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);
  
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService _apiService = ApiService();
  
  SensorData? _temperature;
  SensorData? _pressure;
  SensorData? _airDensity;
  
  bool _isLoading = false;
  String _status = '⏳ Starting...';
  Timer? _updateTimer;
  
  @override
  void initState() {
    super.initState();
    _loadData();
    _startAutoUpdate();
  }
  
  @override
  void dispose() {
    _updateTimer?.cancel();
    super.dispose();
  }
  
  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _status = '⏳ Loading...';
    });
    
    try {
      final results = await Future.wait([
        _apiService.getTemperature(),
        _apiService.getPressure(),
        _apiService.getAirDensity(),
      ]);
      
      setState(() {
        _temperature = results[0];
        _pressure = results[1];
        _airDensity = results[2];
        _status = '● Connected';
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _status = '❌ Error: $e';
        _isLoading = false;
      });
    }
  }
  
  void _startAutoUpdate() {
    _updateTimer = Timer.periodic(const Duration(seconds: 10), (_) => _loadData());
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade100,
      appBar: AppBar(
        title: const Text('🌡️ Sensor BMP280'),
        centerTitle: true,
        flexibleSpace: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFF667eea), Color(0xFF764ba2)],
            ),
          ),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(30),
          child: Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Text(
              _status,
              style: const TextStyle(color: Colors.white, fontSize: 12),
            ),
          ),
        ),
      ),
      body: _isLoading && _temperature == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Cards de valores actuales
                  Row(
                    children: [
                      Expanded(
                        child: SensorCard(
                          title: 'Temperature',
                          value: _temperature?.currentValue ?? 0,
                          unit: '°C',
                          icon: Icons.thermostat,
                          color: Colors.red,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: SensorCard(
                          title: 'Pressure',
                          value: _pressure?.currentValue ?? 0,
                          unit: 'hPa',
                          icon: Icons.compress,
                          color: Colors.blue,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  SensorCard(
                    title: 'Air Density',
                    value: _airDensity?.currentValue ?? 0,
                    unit: 'kg/m³',
                    icon: Icons.air,
                    color: Colors.green,
                  ),
                  
                  const SizedBox(height: 20),
                  
                  // Gráficos
                  if (_temperature != null)
                    SensorChart(data: _temperature!, color: Colors.red),
                  
                  const SizedBox(height: 15),
                  
                  if (_pressure != null)
                    SensorChart(data: _pressure!, color: Colors.blue),
                  
                  const SizedBox(height: 15),
                  
                  if (_airDensity != null)
                    SensorChart(data: _airDensity!, color: Colors.green),
                  
                  const SizedBox(height: 20),
                  
                  // Botón actualizar
                  ElevatedButton.icon(
                    onPressed: _loadData,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Update Data'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      padding: const EdgeInsets.all(15),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}