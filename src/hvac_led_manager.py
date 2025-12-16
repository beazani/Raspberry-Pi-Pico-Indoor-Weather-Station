from machine import Pin

class HVAC_LEDManager:
    def __init__(self, green_pin=15, red_pin=14):
        self.green = Pin(green_pin, Pin.OUT)
        self.red = Pin(red_pin, Pin.OUT)
        self.all_off()

    def set_mode_hvac(self, mode):
        if mode == "COMFORTABLE":
            self.set_comfortable()
        elif mode == "UNCOMFORTABLE":
            self.set_uncomfortable()
        else:
            self.all_off()


    def all_off(self):
        self.green.value(0)
        self.red.value(0)

    def set_comfortable(self):
        self.green.value(1)
        self.red.value(0)

    def set_uncomfortable(self):
        self.green.value(0)
        self.red.value(1)
