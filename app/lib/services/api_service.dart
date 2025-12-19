import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import '../models/sensor_data.dart';

class ApiService {
  static const String baseUrl = 'http://192.168.43.194:5000';
  static const Duration timeoutDuration = Duration(seconds: 10);
  
  Future<SensorData> getTemperature({String range = '-6h'}) async {
    return _getData('/temperature', range, 'Temperature (°C)');
  }
  
  Future<SensorData> getPressure({String range = '-6h'}) async {
    return _getData('/pressure', range, 'Pressure (hPa)');
  }
  
  Future<SensorData> getAirDensity({String range = '-6h'}) async {
    return _getData('/air_density', range, 'Air Density (kg/m³)');
  }
  
  Future<SensorData> _getData(String endpoint, String range, String label) async {
    try {
      String url = '$baseUrl$endpoint?range=$range';
      print(' Calling: $url');
      
      final response = await http.get(Uri.parse(url)).timeout(timeoutDuration);
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return SensorData.fromJson(data, label);
      } else {
        throw Exception('Error ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Connection error: $e');
    }
  }
}