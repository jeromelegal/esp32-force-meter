import time
from machine import Pin

class HX711:
    def __init__(self, dout, pd_sck, gain=128):
        self.pSCK = Pin(pd_sck, Pin.OUT)
        self.pOUT = Pin(dout, Pin.IN)
        self.pSCK.value(0)
        self.offset = 0
        self.scale = 1.0

    def is_ready(self):
        return self.pOUT.value() == 0

    def read(self):
        while not self.is_ready():
            time.sleep_ms(1)
        
        data = 0
        for _ in range(24):
            self.pSCK.value(1)
            data = (data << 1) | self.pOUT.value()
            self.pSCK.value(0)
            
        self.pSCK.value(1)
        self.pSCK.value(0)
        
        if data & 0x800000:
            data -= 0x1000000
            
        return data

    def tare(self, times=15):
        sum_val = 0
        for _ in range(times):
            sum_val += self.read()
        self.offset = sum_val / times

    def get_value(self, times=3):
        sum_val = 0
        for _ in range(times):
            sum_val += self.read()
        return (sum_val / times) - self.offset

    def get_units(self, times=3):
        return self.get_value(times) / self.scale
