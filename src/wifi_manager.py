import network
import time

class WiFiManager:
    def __init__(self, ssid, password, led_manager=None):
        # initialize wifi manager
        # ssid: network name
        # password: network password
        # led_manager: optional LEDManager instance for status indication
        self.ssid = ssid
        self.password = password
        self.led_manager = led_manager
        self.wlan = network.WLAN(network.STA_IF)
        self.connection_attempts = 0
        self.max_attempts = 3
        
        print(f"Wi-Fi Manager initialized for: {ssid}")
    
    def connect(self, timeout=20):
        # connect to wifi network with timeout
        print(f"\nAttempting to connect to: {self.ssid}")
        
        # set LED to connecting pattern if available
        if self.led_manager:
            self.led_manager.set_mode("WIFI_CONNECTING")
        
        # activate interface
        self.wlan.active(True)
        
        # connect if not already connected
        if not self.wlan.isconnected():
            print("Connecting", end="")
            self.wlan.connect(self.ssid, self.password)
            
            # wait for connection with timeout
            start_time = time.time()
            while not self.wlan.isconnected():
                elapsed = time.time() - start_time
                
                if elapsed > timeout:
                    print(f"\nConnection timeout after {timeout} seconds")
                    if self.led_manager:
                        self.led_manager.set_mode("ERROR", duration_ms=2000)
                    return False
                
                print(".", end="")
                time.sleep(0.5)
        
        # connected successfully
        print(f"\nWi-Fi connected!")
        print(f"   IP Address: {self.get_ip()}")
        # print(f"   Subnet Mask: {self.get_subnet()}")
        # print(f"   Gateway: {self.get_gateway()}")
        # print(f"   DNS: {self.get_dns()}")
        
        # set LED to connected pattern
        if self.led_manager:
            self.led_manager.set_mode("WIFI_CONNECTED", duration_ms=3000)
        
        self.connection_attempts = 0
        return True
    
    def disconnect(self):
        # disconnect from wifi
        print("Disconnecting from Wi-Fi...")
        
        if self.led_manager:
            self.led_manager.solid_off()
        
        self.wlan.disconnect()
        self.wlan.active(False)
        print("Wi-Fi disconnected")
    
    def reconnect(self):
        # retry connection
        self.connection_attempts += 1
        
        if self.connection_attempts > self.max_attempts:
            print(f"Max connection attempts ({self.max_attempts}) reached")
            if self.led_manager:
                self.led_manager.indicate_error(self.connection_attempts)
            return False
        
        print(f"\nReconnection attempt {self.connection_attempts}/{self.max_attempts}")
        self.disconnect()
        time.sleep(1)
        return self.connect()
    
    def is_connected(self):
        # check if connected
        return self.wlan.isconnected()
    
    def get_ip(self):
        # get assigned IP address
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        return "Not connected"
    
    def get_subnet(self):
        # get subnet mask
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[1]
        return "Not connected"
    
    def get_gateway(self):
        # get gateway IP
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[2]
        return "Not connected"
    
    def get_dns(self):
        # get DNS server
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[3]
        return "Not connected"
    
    def get_strength(self):
        # get Wi-Fi signal strength

        if self.wlan.isconnected():
            return self.wlan.status('rssi')
        return None
    
    def get_strength_percentage(self):
        # get Wi-Fi signal strength as percentage
        rssi = self.get_strength()
        if rssi is None:
            return 0
        
        # convert RSSI to percentage (approx)
        # RSSI range: -100 (worst) to -30 (best)
        if rssi >= -30:
            return 100
        elif rssi <= -100:
            return 0
        else:
            return int(((rssi + 100) / 70) * 100)
    
    def get_network_info(self):
        # get all network information as dictionary
        return {
            "connected": self.is_connected(),
            "ssid": self.ssid,
            "ip": self.get_ip(),
            "subnet": self.get_subnet(),
            "gateway": self.get_gateway(),
            "dns": self.get_dns(),
            "rssi": self.get_strength(),
            "signal_strength": self.get_strength_percentage(),
            "attempts": self.connection_attempts
        }

# test function
def test_wifi():
    # test Wi-Fi connection (requires config.py)
    print("\n" + "="*50)
    print("Testing Wi-Fi Connection")
    print("="*50)
    
    try:
        import config
        
        wifi = WiFiManager(config.WIFI_SSID, config.WIFI_PASSWORD)
        
        if wifi.connect(timeout=15):
            print("\nWi-Fi test successful!")
            print("\nNetwork Information:")
            info = wifi.get_network_info()
            for key, value in info.items():
                print(f"  {key}: {value}")
            
            # keep connected for 5 seconds
            print("\nStaying connected for 5 seconds...")
            time.sleep(5)
            
            wifi.disconnect()
            return True
        else:
            print("\nWi-Fi test failed")
            return False
            
    except ImportError:
        print("config.py not found or invalid")
        print("Please create config.py from config_template.py")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# run test if executed directly
if __name__ == "__main__":
    test_wifi()