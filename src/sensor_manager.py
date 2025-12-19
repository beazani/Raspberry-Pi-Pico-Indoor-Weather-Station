import time
from machine import I2C, Pin

class WeatherSensor:
    """BMP280 sensor manager for reading temperature and pressure via I2C."""
    def __init__(self, i2c_channel=0, scl_pin=21, sda_pin=20, address=0x76):
        print("Initializing BMP280 sensor...")
        
        # intiialize i2c
        self.i2c = I2C(i2c_channel, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=100000)
        self.address = address
        
        # try to import BMP280 library
        try:
            from bmp280 import BMP280
            self.sensor = BMP280(self.i2c)
            self.connected = True
            print("BMP280 sensor connected successfully")
            
            # test reading
            temp = self.sensor.temperature
            pres = self.sensor.pressure
            print(f"  Test reading: {temp:.1f}°C, {pres:.1f}Pa")
            
        except Exception as e:
            print(f"Failed to initialize BMP280: {e}")
            print("  Check: from bmp280 import BMP280")
            self.connected = False
            self.sensor = None
    
    def read(self):
        """Read temperature and pressure from sensor. Returns tuple: (temp, pressure) or (None, None) on error."""
        if not self.connected or self.sensor is None:
            return None, None
        
        try:
            temp = self.sensor.temperature
            pres = self.sensor.pressure
            
            temperature = round(temp, 1)
            pressure = round(pres, 1)
            
            
            return temperature, pressure
            
        except Exception as e:
            print(f"Sensor read error: {e}")
            return None, None
    
    def read_json(self):
        """Read sensor values as JSON dictionary with timestamp."""
        temp, pres = self.read()
        
        if temp is None:
            return None
        
        return {
            "temperature": temp,
            "pressure": pres,
            "sensor_type": "BMP280",
            "timestamp": time.time()
        }
    
    def is_connected(self):
        """Check if sensor is connected and initialized."""
        return self.connected
    
    def scan_i2c(self):
        """Scan I2C bus for connected devices and detect BMP280."""
        print("Scanning I2C bus...")
        devices = self.i2c.scan()
        
        if devices:
            print(f"Found {len(devices)} I2C device(s):")
            for device in devices:
                print(f"  Address: 0x{device:02x} ({device})")
                
            # BMP280 typically at 0x76 or 0x77
            if 0x76 in devices or 0x77 in devices:
                print("BMP280 detected!")
            else:
                print("BMP280 not found at expected addresses (0x76 or 0x77)")
        else:
            print("No I2C devices found!")
        
        return devices
    
    def get_sensor_info(self):
        """Return sensor type, connection status, and chip information."""    
        if not self.connected:
            return {"type": "Unknown", "connected": False}
        
        try:
            chip_id = self.sensor.chip_id
            return {
                "type": "BMP280",
                "connected": True,
                "chip_id": chip_id,
                "address": hex(self.address),
            }
        except:
            return {"type": "BMP280", "connected": True}


def test_bmp280():
    """Test BMP280 sensor with multiple readings and I2C bus scanning."""
    print("\n" + "="*50)
    print("Testing BMP280 Sensor (Temperature + Pressure ONLY)")
    print("="*50)
    
    sensor = WeatherSensor()
    
    if not sensor.is_connected():
        print("\nSensor not connected. Please check:")
        print("  1. Wiring: SDA→GP0, SCL→GP1, VCC→3V3, GND→GND")
        print("  2. bmp280.py file exists on Pico")
        sensor.scan_i2c()
        return False
    
    print("\nSensor connected!")
    print(f"Sensor info: {sensor.get_sensor_info()}")
    
    print("\nTaking 5 readings (2 seconds apart):")
    print("-" * 40)
    
    for i in range(5):
        temp, pres = sensor.read()
        
        if temp is not None:
            print(f"Reading {i+1}:")
            print(f"  Temperature: {temp} °C")
            print(f"  Pressure: {pres} Pa")
            print("-" * 20)
        else:
            print(f"Reading {i+1} failed")
        
        time.sleep(2)
    
    print("\nBMP280 test complete!")
    return True


if __name__ == "__main__":
    test_bmp280()