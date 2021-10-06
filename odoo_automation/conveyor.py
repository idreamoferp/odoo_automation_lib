from odoo_automation import machine
import logging, configparser, threading, time
from simple_pid import PID

_logger = logging.getLogger(__name__)
class Conveyor(object):
    def __init__(self, config):
        self.config = config
        self._logger = logging.getLogger(config['name'])
        self.read_config()        
        
        self.run_status = False
        self.e_stop_status = False
        
        self.current_ipm = 0
        self.last_tach_tick = 0
        
        
        
        self._logger.info("INIT Compleete.")
        pass
    
    def read_config(self):
        self._logger.info("Reading Config file")
        self.name = self.config['name']
        self._set_ipm = float(self.config['set_speed'])
        self.uom = self.config['uom']
        self.uom_per_tick = float(self.config['uom_per_tick'])
        P = float(self.config['P'])
        I = float(self.config['I'])
        D = float(self.config['D'])
        L_limit = float(self.config['PID_L_limit'])
        U_limit = float(self.config['PID_U_limit'])
        
        self.pid_controller = PID(P, I, D, setpoint=0)
        self.pid_controller.output_limits = (L_limit, U_limit)
        
        return True
        
    def save_config(self):
        self.config['set_speed'] = self._set_ipm
        self.config['uom_per_tick'] = self.uom_per_tick
        self.config['P'] =  self.pid_controller.Kp
        self.config['I'] = self.pid_controller.Ki
        self.config['D'] =  self.pid_controller.Kd
        self.config['PID_L_limit'] = self.pid_controller.pid.output_limits[0]
        self.config['PID_U_limit'] = self.pid_controller.pid.output_limits[1]
        return self.config
        
    @property
    def set_ipm(self):
        return self.pid_controller.setpoint
    
    @set_ipm.setter
    def set_ipm(self, value):
        self.pid_controller.setpoint = value
        pass    
        
    def get_config(self):
        config = configparser.ConfigParser()
        config[self.name] = {}
        config[self.name]['set_ipm'] = self.set_ipm
        config[self.name]['pid_p'] = self.pid_p
        config[self.name]['pid_i'] = self.pid_i
        config[self.name]['pid_d'] = self.pid_d
        return config
    
    def start(self):
        if not self.run_status:
            self._logger.info("Started at %s %s" % (self._set_ipm, self.uom))
        self.run_status = True
        
        pass
    
    def stop(self):
        if self.run_status:
            self._logger.info("Stopped.")
        self.run_status = False
        self.last_tach_tick = 0
        
        pass
    
    def e_stop(self):
        #this will loop constantly while the e-stop is depressed.
        if not self.e_stop_status:
            self.stop()
            self.e_stop_status = True
            
            #abruptly shutdown the main loop thread.
            #in the main machine config, setup all the i/o to render safe the machine.
            #self.main_machine_thread.stop()
            self._logger.warn("Conveyor has entered the E-STOP state.")
        pass
    
    def e_stop_reset(self):
        if self.e_stop_status:
            self.run_status = False
            self.e_stop_status = False
            
            #re-boot the main loop thread
            #self.main_machine_thread.start()
            self._logger.warn("Conveyor has reset the E-STOP state.")
        pass
    
    def run_loop(self):
        while True:
            try:
                if self.current_ipm > 0:
                    calc_output = self.pid_controller(self.current_ipm)
                    calc_output = calc_output * -1
                    self.set_speed(calc_output)
                    
            except Exception as e:
                self._logger.warn(e)
            
            time.sleep()
            
    def tach_tick(self):
        calc_output = self.pid_controller(self.current_ipm)
        calc_output = calc_output * -1
        self.set_speed(calc_output)
            
    def set_speed(self, freq_offset):
        return True
        
    def quit(self):
        
        self._logger.info("Shutdown")
            
class Diverter(object):
    def __init__(self, name):
        self._logger = logging.getLogger(name)
        self.busy = False
        
        #dict of lanes this diverter is connected to for status polling
        self.lanes = {}
        
        #this dict contains the methods to call for each lane to destination lanes.
        #the key to the dict is the current lane id, the value is a dict of destination keys and value methods to call.
        #{'work':{'work': method_to_call,'bypass':method_to_call},}
        self.lane_diverter = {}
        self.conveyor = None
        self._logger.info("INIT Compleete.")
        pass
    
    def divert(self, current_lane, destination_lane):
        
        #wait for destination lane status to be true
        while destination_lane.get_status():
            time.sleep(10)
        
        self.busy = True    
        
        #call the method stored in the lane_diverter for this path
        self.lane_diverter[current_lane.type][destination_lane.type]()
        
        
        return True
        
    def clear_divert(self):
        self.busy = False
        pass

import board, pulseio, digitalio
import RPi.GPIO as GPIO  

class conv_1(Conveyor):
    def __init__(self, name="conveyor_test"):
        super(conv_1, self).__init__(name=name)
        
        self.pid_controller.Kp = .4
        self.pid_controller.Ki = .05
        self.pid_controller.Kd = 6
        
        self.inch_per_rpm = 4.75
        
        GPIO.setmode(GPIO.BCM)  
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(23, GPIO.FALLING, callback=self.tach_tick)
        
        GPIO.setup(12,GPIO.OUT)
        self.motor_p = GPIO.PWM(12,5000)
        self.motor_duty = 40
        pass 
    
    def set_speed(self, freq_offset):
        duty = self.motor_duty + freq_offset
        
        if duty > 100:
            duty = 100
            
        if duty < 0:
            duty = 0
        # print("duty = %s" % duty)
        
        self.motor_p.ChangeDutyCycle(duty)
        self.motor_duty = duty
        
        return super(conv_1, self).set_speed(freq_offset=freq_offset)
    
    def start(self):
        self.motor_p.start(self.motor_duty)
        return super(conv_1, self).start()
    
    def stop(self):
        self.motor_p.stop()
        return super(conv_1, self).stop()
    
    def tach_tick(self, ch):
        new_tick = time.time()
        if self.last_tach_tick == 0:
            self.last_tach_tick = new_tick
            return
        
        pulse_len = new_tick - self.last_tach_tick
        # if pulse_len > 0.8:
        self.last_tach_tick = new_tick
        self.current_ipm = round(pulse_len * self.inch_per_rpm, 5)
        print("cipm = %s" % self.current_ipm)
    
        return super(conv_1, self).tach_tick()

if __name__ == "__main__":
    c = conv_1()
    c.set_ipm=10
    c.start()
    
    while 1:
        time.sleep(10)
    