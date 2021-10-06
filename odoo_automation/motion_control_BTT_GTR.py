from . import motion_control as mc
import time, configparser, threading, logging

class MotonControl(mc.MotonControl):
    def __init__(self, com_port):
        self._logger = logging.getLogger("Marlin MC %s" % (com_port.name))
        super(MotonControl, self).__init__()
        
        
        self.comm = com_port
        self.comm_lock = threading.Lock()
        
        self.axis_to_home = []
        
        
        #launch status refresher
        self.status_refresh = 0.5
        self.read_thread = threading.Thread(target=self.read_buffer, daemon=True)
        self.read_thread.start()
        
        self.errors = []
        pass
   
    
    def read_buffer(self):
        while True:
            try:
                # self._buffer = self.comm.read(1)
                
                buffer_line = self.comm.readline().decode('utf-8').replace('\r\n',"")
                self._logger.debug(buffer_line.replace("\n", ""))
                
                if buffer_line == 'ok' or "":
                    continue
                
                if "echo" in buffer_line:
                    message_parts = buffer_line.split(":")
                    
                    if message_parts[1] == "Homing Failed\n":
                        self.status = "Homing Failed"
                        self.is_home = False
                    
                    if message_parts[1] == "Homing Success\n":
                        self.is_home = True
                        
                    if message_parts[1] == "busy":
                        self.status = "Run"
                        
                    if message_parts[1] == "idle":
                        self.status = "Idle"
                    continue
                
                #"Error:Failed to reach target"
                
            # except serial.SerialException as e:
            except Exception as e:
                self._logger.warn("%s while reading buffer" % e)
        
    def send_command(self, command):
        self._logger.debug("Sending Command - %s" % (command))
        command += "\r\n"
        command = command.encode('utf-8')
        
        with self.comm_lock:
            try:
                bytes_written = self.comm.write(command)
                self._logger.debug("Sending Command - %s - SENT" % (command))
                return True
            except Exception as e:
                
                self._logger.error(e)
                return False
       
    def _goto_position(self,x=False,y=False,z=False,a=False,b=False,feed=False, wait=False):
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
        
        command += "\nM400\nM118 E1 idle\n" 
        self.status='Run'
        self.send_command(command)
            
        return super(MotonControl, self)._goto_position(x,y,z,a,b,feed,wait)
        
    def goto_position_rel(self,x=False,y=False,z=False,a=False,b=False,feed=False, wait=False):
        self.send_command("G91")
        return self._goto_position(x,y,z,a,b,feed,wait)
    
    def goto_position_abs(self,x=False,y=False,z=False,a=False,b=False,feed=False, wait=False):
        self.send_command("G90")
        return self._goto_position(x,y,z,a,b,feed,wait)
        
    def work_offset(self,x=0,y=0,z=0,a=0,b=0):
        if x+y+z+a+b == 0:
            #set work offset to machine home 
            self.send_command("G54")
            return super(MotonControl,self).work_offset(x,y,z,a,b)
            
        self.send_command("G10P2L2x%sy%sz%s" % (x,y,z))
        self.send_command("G55")
        return super(MotonControl,self).work_offset(x,y,z,a,b)
    
    def home(self, force=False):
        if not self.is_home or force:
            self.status = "Homing"
            command = "G28"
            for axis in self.axis_to_home:
                command += axis
            
            result = self.send_command(command)
            
            stop_waiting = True
            while stop_waiting:
                self._logger.debug("Waiting to home - %s" % (self.is_home))
                if self.is_home:
                    stop_waiting = False
                
                if self.status == "Homing Failed":
                    stop_waiting = False
                
                time.sleep(.1)
        self._logger.info("Home Operation - %s" % (self.is_home))
        self.status = "Idle"
        return self.is_home

    def quit(self):
        self.comm.close()
        pass
    
    def wait_for_movement(self):
        start_wait_time = time.time()
        while self.status != 'Idle':
            
            time.sleep(0.1)
        self._logger.debug("return from wait.")
        return super(MotonControl, self).wait_for_movement()
    
if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s - %(message)s",datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.DEBUG)
    import serial
    port = serial.Serial('/dev/ttyACM0', baudrate=115200)
    g = MotonControl(port)
    
    g.axis_to_home = ["Y", "Z"]
    
    g.home()
    
    while 1:
        if g.status == "Idle":
            g.goto_position_abs(x=0.0,y=0.0,z=0.0,feed=5000)
            g.goto_position_abs(y=500,feed=1000, wait=1)
            g.goto_position_abs(z=180,feed=2000)
            g.goto_position_rel(x=100,y=-8,feed=1500)
            g.goto_position_rel(z=-10,x=-100,y=+80,feed=1500)
            g.goto_position_rel(z=-10,x=100,y=-80,feed=1500)
            g.goto_position_rel(z=-10,x=-100,y=+80,feed=1500)
            g.goto_position_rel(z=-10,x=100,y=-80,feed=1500)
            g.goto_position_abs(z=0.0,y=450,feed=4000)
            g.goto_position_abs(x=0.0,y=0.0,feed=5000)

        time.sleep(.5)