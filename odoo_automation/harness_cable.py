from smbus2 import SMBus, i2c_msg

#cables must all have an i2c eeprom addressed to 0x50
i2c_address = 0x50

#0x00 - 0x0F = Cable part number
#0x10 - 0x1F = Cable serial number
#0x20 - 0x3F = Cable mfg date (32 bit integer of python epoch time)
#0x40 - 0x5F = Flags register
#0x60 - 0x6F = cable test count
#0x60 - 0x9F = reserved
#0xA0 - 0xFF = Cable calibration data (optional)

class HarnessCable():
    def __init__(self, bus_id):
        self.i2c_bus = SMBus(bus_id)
        self.harness_connected = False
        self.part_number = False
        self.serial_number = False
        pass
    
    def read_eprom_block(self, address, length):
        try:
            #send control word to read from address 0x0000
            self.i2c_bus.i2c_rdwr(i2c_msg.write(i2c_address, [0, 0]))
            
            #read in 16 bytes of part number
            data = self.i2c_bus.read_i2c_block_data(i2c_address, 0, 16)
            
            self.harness_connected = True
            
        except Exception:
            self.clear_harness()
            return None
            
        return bytearray(data)
        
    def read_part_number(self):
        data = self.read_eprom_block(0x0, 16)
        if data:
            self.part_number = data.decode("utf-8").strip()
            return self.part_number
        
        return None
    
    def clear_harness(self):
        self.harness_connected = False
        self.part_number = False
        self.serial_number = False
        
if __name__ == "__main__":
    h = HarnessCable(bus_id=1)
    
    #[0x39,0x39,0x39,0x2D,0x31,0x32,0x33,0x34,0x2D,0x30,0x30] 
    