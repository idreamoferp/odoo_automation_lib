import automation, conveyor, automation_web
import logging, odoorpc, threading, time, argparse, configparser
import digitalio, board, busio #blinka libs
import motion_control_grbl as motion_control
from adafruit_mcp230xx.mcp23017 import MCP23017
i2c = busio.I2C(board.SCL, board.SDA)
mcp20 = MCP23017(i2c, address=0x20)
#mcp21 = MCP23017(i2c, address=0x21)


#setup logger
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s - %(message)s",datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.INFO)
_logger = logging.getLogger("Test Machine")

class TestMachine(automation_web.Automation_Webservice, automation.MRP_Automation):
    
    def __init__(self, api, asset_id):
        
        
        #init conveyor for this machine
        self.conveyor_1 = Conveyor_1()
        self.conveyor_1.set_ipm = 10
        
        #setup button pins
        self.button_start_input = digitalio.DigitalInOut(board.D20)
        self.button_start_input.direction = digitalio.Direction.INPUT
        self.button_start_input.pull = digitalio.Pull.UP
        
        self.button_stop_input = digitalio.DigitalInOut(board.D19)
        self.button_stop_input.direction = digitalio.Direction.INPUT
        self.button_stop_input.pull = digitalio.Pull.UP
        
        self.button_estop_input = digitalio.DigitalInOut(board.D21)
        self.button_estop_input.direction = digitalio.Direction.INPUT
        self.button_estop_input.pull = digitalio.Pull.UP
        
        self.button_start_led = digitalio.DigitalInOut(board.D17)
        self.button_start_led.direction = digitalio.Direction.OUTPUT
        
        self.button_warn_led = digitalio.DigitalInOut(board.D27)
        self.button_warn_led.direction = digitalio.Direction.OUTPUT
        
        self.button_estop_led = digitalio.DigitalInOut(board.D22)
        self.button_estop_led.direction = digitalio.Direction.OUTPUT
        
        super(TestMachine, self).__init__(api, asset_id)
        
        self.button_input_thread = threading.Thread(target=self.button_input_loop, daemon=True)
        self.button_input_thread.start()
        
        #init route lanes
        
        self.route_lanes = [MRP_Carrier_Lane_0(self.api, self), MRP_Carrier_Lane_1(self.api, self)]
        
        self.motion_control = motion_control.MotonControl('/dev/serial0')
        self.motion_control.home()
        self.goto_default_location()
        
        _logger.info("Machine INIT Compleete.")
        self.start_webservice()
        return
        
    def button_input_loop(self):
        while True:
            if not self.button_start_input.value:
                self.button_start()
            
            if not self.button_stop_input.value:
                self.button_stop()
                
            if not self.button_estop_input.value:
                self.e_stop()
                
            if self.button_estop_input.value and self.e_stop_status == True:
                self.e_stop_reset() 
                
            time.sleep(0.1)
            
    def indicator_start(self, value):
        self.button_start_led.value = value
        return super(TestMachine, self).indicator_start(value)
    
    def indicator_warn(self, value):
        self.button_warn_led.value = value
        return super(TestMachine, self).indicator_warn(value)
        
    def indicator_e_stop(self, value):
        self.button_estop_led.value = not value
        return super(TestMachine, self).indicator_e_stop(value)
        
    
    #Button inputs
    def button_start(self):
        self.conveyor_1.start()
        return super(TestMachine, self).button_start()
    
    def button_stop(self):
        self.conveyor_1.stop()
        return super(TestMachine, self).button_stop()
    
    def e_stop(self):
        #put render safe i/o here.
        self.conveyor_1.e_stop()
        return super(TestMachine, self).e_stop()
    
    def e_stop_reset(self):
        #put reboot i/o here
        self.conveyor_1.e_stop_reset()
        return super(TestMachine, self).e_stop_reset()
        
    def quit(self):
        #set indicators to safe off state.
        self.indicator_start(False)
        self.indicator_warn(False)
        
        #send quit signals to sub components
        self.conveyor_1.quit()
        return super(TestMachine, self).quit()  
        
    #motion and machine controls
    def goto_default_location(self):
        self.motion_control.goto_position_abs(y=325,z=0.0,feed=6000)
    
        
class MRP_Carrier_Lane_0(automation.MRP_Carrier_Lane):
    def __init__(self, api, mrp_automation_machine):
        self._logger = logging.getLogger("Carrier Lane 0")
        super(MRP_Carrier_Lane_0, self).__init__(api, mrp_automation_machine)
        
        self.input_ingress = mcp20.get_pin(8)
        self.input_ingress.direction = digitalio.Direction.INPUT
        self.input_ingress.pull = digitalio.Pull.UP
        
        self.ingress_end_stop = mcp20.get_pin(9)
        self.ingress_end_stop.direction = digitalio.Direction.INPUT
        self.ingress_end_stop.pull = digitalio.Pull.UP
        
        self.output_ingress_gate = mcp20.get_pin(7)
        self.output_ingress_gate.direction = digitalio.Direction.OUTPUT
        self.output_ingress_gate.value = False
        
        self.output_carrier_capture = mcp20.get_pin(6)
        self.output_carrier_capture.direction = digitalio.Direction.OUTPUT
        self.output_carrier_capture.value = False
        
        self._logger.info("Lane INIT Complete")
        pass
    
    def goto_position_abs(self, y=0,z=0,a=0, feed=0):
        return self.mrp_automation_machine.motion_control.goto_position_abs(x=a,y=y,z=z,feed=3000)
    def goto_position_rel(self, y=0,z=0,a=0,feed=0):
        return self.mrp_automation_machine.motion_control.goto_position_rel(x=a,y=y,z=z,feed=3000)
    
    #main loop functions
    def preflight_checks(self):
        #check that the machine is ready to accept a product.
        if not self.ingress_end_stop.value:
            self._logger.warn("Carrier End Stop trigger, a carrier may be trapped in the machine.")
            return False
        
        return True
        
    def ingress_trigger(self):
        return not self.input_ingress.value
        
    def process_ingress(self):
        
        #open ingress gate
        self.output_ingress_gate.value = True
        self._logger.info("Machine opened ingress gate, waiting for product to trigger end stop")
        
        #positioning machine to lane zero
        self.mrp_automation_machine.motion_control.work_offset(y=550)
        self.goto_position_abs(0,0,0,feed=5000)
        
        #wait for ingress end stop trigger
        time_out = time.time()
        while self.ingress_end_stop.value:
            if time_out + 60 < time.time():
                self.output_ingress_gate.value = True
                self.warn = True
                self._logger.warn("Timeout waiting for ingress end stop trigger")
                return False
            #throttle wait peroid.
            time.sleep(0.5)
        
        self._logger.info("Product triggered endstop, closing ingress gate, capture product carrier")    
        self.output_ingress_gate.value = False
        self.output_carrier_capture.value = True
        
        self.mrp_automation_machine.motion_control.wait_for_movement()
        
        return True
        
    def process_egress(self):
        self._logger.info("Machine opening egress gate, waiting to clear end stop trigger.")
        
        #put the machine in a safe location
        self.goto_position_abs(z=0,feed=8000)
        
        time.sleep(1)
        self.mrp_automation_machine.motion_control.wait_for_movement()
        #set the machine offsets back to machine cord.
        self.mrp_automation_machine.motion_control.work_offset(y=0)
        
        #configure diverter for the destination
        destination_lane = self.currernt_carrier.carrier_history_id.route_node_lane_dest_id
        self.mrp_automation_machine.conveyor_1.diverter.divert(self.route_node_lane, destination_lane)
        
        #release carrier capture
        self.output_carrier_capture.value = False
        
        #wait for egress end stop trigger
        time_out = time.time()
        while not self.ingress_end_stop.value:
            if time_out + 60 < time.time():
                self._logger.warn("Timeout waiting for egress end stop trigger.")
                return False
            #throttle wait peroid.
            time.sleep(0.5)
        
        #free the diverter for other operations
        self.mrp_automation_machine.conveyor_1.diverter.clear_divert()
        self.mrp_automation_machine.goto_default_location()
        return True
        
    def quit(self):
        super(MRP_Carrier_Lane_0, self).quit()
            
        self.output_ingress_gate.value=0
        self.output_carrier_capture.value=0
        return True
    
class MRP_Carrier_Lane_1(automation.MRP_Carrier_Lane):
    def __init__(self, api, mrp_automation_machine):
        super(MRP_Carrier_Lane_1, self).__init__(api, mrp_automation_machine)
        self._logger = logging.getLogger("Carrier Lane 1")
        self._logger.info("Lane INIT Complete")
        pass

import RPi.GPIO as GPIO
class Conveyor_1(conveyor.Conveyor):
    
    def __init__(self):
        super(Conveyor_1, self).__init__(name="conveyor_1")
        
        self.pid_controller.Kp = .45
        self.pid_controller.Ki = .05
        self.pid_controller.Kd = 6
        
        self.inch_per_rpm = 4.75
        
        GPIO.setmode(GPIO.BCM)  
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(23, GPIO.RISING, callback=self.tach_tick)
        
        GPIO.setup(12,GPIO.OUT)
        self.motor_p = GPIO.PWM(12,5000)
        self.motor_p.start(0)
        self.motor_duty = 40
        
        #setup diverter logic
        self.diverter = divert_1("Conveyor_1_Diverter")
        self.diverter.lane_diverter = {'work':{'work':self.diverter_work_work,'bypass':self.diverter_work_bypass},'bypass':{'work':self.diverter_bypass_work,'bypass':self.diverter_bypass_bypass}}
        pass
    
    def set_speed(self, freq_offset):
        duty = self.motor_duty + freq_offset
        
        if duty > 100:
            duty = 100
            
        if duty < 0:
            duty = 0
        
        self.motor_p.ChangeDutyCycle(duty)
        self.motor_duty = duty
        
        return super(Conveyor_1, self).set_speed(freq_offset=freq_offset)
    
    def start(self):
        self.motor_p.ChangeDutyCycle(self.motor_duty)
        return super(Conveyor_1, self).start()
    
    def stop(self):
        self.motor_p.ChangeDutyCycle(0)
        return super(Conveyor_1, self).stop()
    
    def tach_tick(self, ch):
        new_tick = time.time()
        if self.last_tach_tick == 0:
            self.last_tach_tick = new_tick
            return
        
        pulse_len = new_tick - self.last_tach_tick
        if pulse_len > 0.8:
            self.last_tach_tick = new_tick
            self.current_ipm = round(pulse_len * self.inch_per_rpm, 1)
            self._logger.debug("Current IPM - %s" %(self.current_ipm))
            return super(Conveyor_1, self).tach_tick()

    def diverter_work_work(self):
        _logger.info("Setting Diverter from Work to Work")
        pass
    
    def diverter_work_bypass(self):
        _logger.info("Setting Diverter from Work to Bypass")
        pass
    
    def diverter_bypass_work(self):
        _logger.info("Setting Diverter from Bypass to Work")
        pass
    
    def diverter_bypass_bypass(self):
        _logger.info("Setting Diverter from Bypass to Bypass")
        pass
    
    def quit(self):
        self.stop()
        self.motor_p.stop()
        return super(Conveyor_1, self).quit()  
        
class divert_1(conveyor.Diverter):
    def clear_divert(self):
        time.sleep(5)
        return super(divert_1, self).clear_divert()
    

#startup this machine
if __name__ == "__main__":
    
    #odoo api settings, TODO: move these to a server_config file
    server = "esg-beta.idreamoferp.com" #"usboiepxd01" 
    port = 80
    database = "ESG_Beta_1-0"
    user_id = "equipment_072"
    password = "1q2w3e4r"
    
    #create instance of odooRPC clinet with these settings
    odoo = odoorpc.ODOO(server, port=port)
    
    #attempt a login to odoo server to init the api
    try:
        odoo.login(database, user_id, password)
    except Exception as e:
        _logger.error("Error logging in to odoo server" + e)
    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--equipment-id', type=int, help='ODOO Maintence Equipment ID')
    args = parser.parse_args()
    
    #create instance of this test machine, and start its engine
    test_machine = TestMachine(api=odoo, asset_id=args.equipment_id)

    while True:
        time.sleep(100)
    pass

