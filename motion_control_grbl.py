import motion_control as mc
import serial
import time
import configparser
import threading
error_messages = {
    "1": "G-code words consist of a letter and a value. Letter was not found.", 
    "2":"Numeric value format is not valid or missing an expected value.",
    "3":"Grbl '$' system command was not recognized or supported.",
    "4":"Negative value received for an expected positive value.",
    "5":"Homing cycle is not enabled via settings.",
    "6":"Minimum step pulse time must be greater than 3usec",
    "7":"EEPROM read failed. Reset and restored to default values.",
    "8":"Grbl '$' command cannot be used unless Grbl is IDLE. Ensures smooth operation during a job.",
    "9":"G-code locked out during alarm or jog state",
    "10":"Soft limits cannot be enabled without homing also enabled.",
    "11":"Max characters per line exceeded. Line was not processed and executed.",
    "12":"(Compile Option) Grbl '$' setting value exceeds the maximum step rate supported.",
    "13":"Safety door detected as opened and door state initiated.",
    "14":"(Grbl-Mega Only) Build info or startup line exceeded EEPROM line length limit.",
    "15":"Jog target exceeds machine travel. Command ignored.",
    "16":"Jog command with no '=' or contains prohibited g-code.",
    "17":"Laser mode requires PWM output.",
    "20":"Unsupported or invalid g-code command found in block.",
    "21":"More than one g-code command from same modal group found in block.",
    "22":"Feed rate has not yet been set or is undefined.",
    "23":"G-code command in block requires an integer value.",
    "24":"Two G-code commands that both require the use of the XYZ axis words were detected in the block.",
    "25":"A G-code word was repeated in the block.",
    "26":"A G-code command implicitly or explicitly requires XYZ axis words in the block, but none were detected.",
    "27":"N line number value is not within the valid range of 1 - 9,999,999.",
    "28":"A G-code command was sent, but is missing some required P or L value words in the line.",
    "29":"Grbl supports six work coordinate systems G54-G59. G59.1, G59.2, and G59.3 are not supported.",
    "30":"The G53 G-code command requires either a G0 seek or G1 feed motion mode to be active. A different motion was active.",
    "31":"There are unused axis words in the block and G80 motion mode cancel is active.",
    "32":"A G2 or G3 arc was commanded but there are no XYZ axis words in the selected plane to trace the arc.",
    "33":"The motion command has an invalid target. G2, G3, and G38.2 generates this error, if the arc is impossible to generate or if the probe target is the current position.",
    "34":"A G2 or G3 arc, traced with the radius definition, had a mathematical error when computing the arc geometry. Try either breaking up the arc into semi-circles or quadrants, or redefine them with the arc offset definition.",
    "35":"A G2 or G3 arc, traced with the offset definition, is missing the IJK offset word in the selected plane to trace the arc.",
    "36":"There are unused, leftover G-code words that aren't used by any command in the block.",
    "37":"The G43.1 dynamic tool length offset command cannot apply an offset to an axis other than its configured axis. The Grbl default axis is the Z-axis.",
    "38":"Tool number greater than max supported value."
        }
        
class MotonControl(mc.MotonControl):
    def __init__(self, port, baud=115200):
        super(MotonControl, self).__init__()
        
        self.comm = serial.Serial(port ,baud)
        self.comm_lock = threading.Lock()
        
        self.soft_reset()
        
        self.grbl_version = False
        
        self.actual_feedrate = 0.0
        self.actual_spindle = 0.0
        self.override_feed = 100
        self.override_rapids = 100
        self.override_spindle = 100
        
        self.errors = []
        
        #wakeup grbl and flush
        self.comm.write(b"\r\n\r\n")
        time.sleep(2)   # Wait for grbl to initialize
        self.comm.flushInput()  # Flush startup text in serial input
        
        #launch status refresher
        self.status_refresh = 0.25
        self.status_thread = threading.Thread(target=self.status_update, daemon=True)
        self.status_thread.start()
        
    def status_update(self):
        while True:
            while self.comm.in_waiting > 0:
                try:
                    with self.comm_lock:
                        #read in entire serial buffer.
                        if self.comm.in_waiting > 0:
                            command = "?"
                            self.comm.write(command.encode('utf-8'))
                        stat = self.comm.readline().decode('utf-8').replace('\r\n',"")
                        
                    
                    
                    if stat == 'ok' or "":
                        continue
                    
                    if "<" in stat:
                        self.parse_status(stat)
                        continue
                        
                    #if "error" in stat:
                    #    continue
                    
                    if "Grbl" in stat:
                        version = stat.split(" ")
                        self.grbl_version = version[1]
                        continue
                    
                    print(stat)
                except Exception as e:
                    print(e)
            
            time.sleep(self.status_refresh)
    
    def parse_status(self, status_message):
        try:
            stat = status_message.replace("<","").replace(">","").split("|")
            
            self.status = stat[0]
            stat.pop(0)
            
            for status in stat:
                this = status.split(":")
                if this[0] == "MPos":
                    xyz = this[1].split(",")
                    self.mach_position_x = float(xyz[0])
                    self.mach_position_y = float(xyz[1])
                    self.mach_position_z = float(xyz[2])
                    continue
                    
                if this[0] == "WCO":
                    xyz = this[1].split(",")
                    self.home_offset_x = xyz[0]
                    self.home_offset_y = xyz[1]
                    self.home_offset_z = xyz[2]
                    continue
                
                if this[0] == "FS":
                    xyz = this[1].split(",")
                    self.actual_feedrate = xyz[0]
                    self.actual_spindle = xyz[1]
                    continue
                
                if this[0] == "Pn":
                    Pins = this[1].split(",")
                    continue
                
                if this[0] == "Ov":
                    xyz = this[1].split(",")
                    self.override_feed = xyz[0]
                    self.override_rapids = xyz[1]
                    self.override_spindle = xyz[2]
                    continue
                
                drink_me=1
        except Exception as e:
            print(e)
            
        pass
    
    def parse_error(self, error_message):
        
        message = error_message.split(":")
        
        pass
    
    def soft_reset(self):
        self.comm.write('\030\r\n'.encode("utf-8"))
        time.sleep(1)
        print(self.send_command("$X\r\n"))
        
    def send_command(self, command):
        res = ""
        with self.comm_lock:
            self.comm.write(command.encode('utf-8') )
            self.comm.write(b'\r\n')
            res = self.comm.readline().decode('utf-8').replace('\r\n',"")
               
        return res
       
    def _goto_position(self,x=False,y=False,z=False,a=False,b=False,feed=False):
        command = ""
        if not isinstance(x, bool):
            command += "X%s " % x
        if not isinstance(y, bool):
            command += "Y%s " % y
        if not isinstance(z, bool):
            command += "Z%s " % z
        if not isinstance(feed, bool):
            command = "G01" + command
            command += "F%s " % feed
        else:
            command = "G0" + command
            
        result = self.send_command(command)
            
        return super(MotonControl, self)._goto_position(x,y,z,a,b,feed)
        
    def goto_position_rel(self,x=False,y=False,z=False,a=False,b=False,feed=False):
        self.send_command("G91")
        return self._goto_position(x,y,z,a,b,feed)
    
    def goto_position_abs(self,x=False,y=False,z=False,a=False,b=False,feed=False):
        self.send_command("G90")
        return self._goto_position(x,y,z,a,b,feed)
        
    def work_offset(self,x=0,y=0,z=0,a=0,b=0):
        if x+y+z+a+b == 0:
            #set work offset to machine home 
            self.send_command("G54")
            return super(MotonControl,self).work_offset(x,y,z,a,b)
            
        self.send_command("G10P2L2x%sy%sz%s" % (x,y,z))
        self.send_command("G55")
        return super(MotonControl,self).work_offset(x,y,z,a,b)
    
    def home(self):
        self.send_command("$H")
        self.send_command("G92x0y0z0")
        
        return super(MotonControl, self).home()

    def quit(self):
        self.soft_reset()
        pass
    
    def wait_for_movement(self):
        while self.status == 'Run':
            time.sleep(0.1)
            
        return super(MotonControl, self).wait_for_movement()
    
def new_config():
    config = configparser.ConfigParser()
    config['GRBL'] = {}
    config['GRBL']["$0"] = "10"   #step pulse uS
    config['GRBL']["$1"] = "25"   #step idle uS
    config['GRBL']["$2"] = "0"    #step port invert mask
    config['GRBL']["$3"] = "0"    #dir port inver mask
    config['GRBL']["$4"] = "0"    #enable port invert mask
    config['GRBL']["$5"] = "0"    #limit port invert mask
    config['GRBL']["$6"] = "0"    #probe invert mask
    config['GRBL']["$10"] = "1"   #status report invert mask
    config['GRBL']["$11"] = "0.010" #junction deviation, mm
    config['GRBL']["$12"] = "0.002" #arc tolerance, mm
    config['GRBL']["$13"] = "0"   #report inches
    config['GRBL']["$20"] = "0"   #soft limits
    config['GRBL']["$21"] = "0"   #hard limits
    config['GRBL']["$22"] = "1"   #homing cycle
    config['GRBL']["$23"] = "0"   #homing dir invert mask
    config['GRBL']["$24"] = "25.0"    #homing feed mm/min
    config['GRBL']["$25"] = "500.0"   #homing seek mm/min
    config['GRBL']["$26"] = "250" #debounce mS
    config['GRBL']["$27"] = "1.0" #homing pulloff (mm)
    config['GRBL']["$30"] = "1000.0" # max spindle (rpm)
    config['GRBL']["$31"] = "0.0"     #min spindle (rpm)
    config['GRBL']["$32"] = "0"       #laser mode
    config['GRBL']["$100"] = "250.0"  #X Setps/mm
    config['GRBL']["$101"] = "250.0"  #Y steps/mm
    config['GRBL']["$102"] = "250.0"  #Z steps/mm
    config['GRBL']["$110"] = "500.0"  #X max feed mm/min
    config['GRBL']["$111"] = "500.0"  #Y max feed mm/min
    config['GRBL']["$112"] = "500.0"  #Z max feed mm/min
    config['GRBL']["$120"] = "10.0"   #X accel mm/sec2
    config['GRBL']["$121"] = "10.0"   #Y accel mm/sec2
    config['GRBL']["$122"] = "10.0"   #Z accel mm/sec2
    config['GRBL']["$130"] = "200.0"  #X max travel mm
    config['GRBL']["$131"] = "200.0"  #Y max travel mm
    config['GRBL']["$132"] = "200.0"  #Z max travel mm
    
    return config
    
    
if __name__ == "__main__":
    
    
    g = MotonControl("/dev/serial0")
    
    
    g.home()
    
    while 1:
        if g.status == "Idle":
            g.goto_position_abs(x=0.0,y=0.0,z=0.0,feed=5000)
            g.goto_position_abs(y=480,feed=5000)
            g.goto_position_abs(z=180,feed=2000)
            g.goto_position_rel(x=100,y=-8,feed=1500)
            g.goto_position_rel(z=-10,x=-100,y=+80,feed=1500)
            g.goto_position_rel(z=-10,x=100,y=-80,feed=1500)
            g.goto_position_rel(z=-10,x=-100,y=+80,feed=1500)
            g.goto_position_rel(z=-10,x=100,y=-80,feed=1500)
            g.goto_position_abs(z=0.0,y=450,feed=4000)
            g.goto_position_abs(x=0.0,y=0.0,feed=5000)
        
        print("[%s] %s, %s, %s - %s" % (g.status, g.position_x, g.position_y, g.position_z, g.actual_feedrate))
        time.sleep(.5)