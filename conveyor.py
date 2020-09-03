import machine
import logging


class Conveyor(object):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.current_ipm = 0
        self.run_status = False
        self.e_stop_status = False
        self._logger.info("INIT Compleete.")
        pass
        
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
        self.run_status = True
        pass
    
    def stop(self):
        self.run_status = False
        self.last_tach_tick = 0
        pass
    
    def e_stop(self):
        #this will loop constantly while the e-stop is depressed.
        if not self.e_stop_status:
            self.run_status = False
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
    
class Diverter(object):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        
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
        
        
    