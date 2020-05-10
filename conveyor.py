import machine

class Conveyor(machine.Machine):
    def __init__(self):
        self.current_ipm = 0
        self.run_status = False
        self.e_stop_status = False
        pass
    
    def e_stop(self):
        #this will loop constantly while the e-stop is depressed.
        if not self.e_stop_status:
            self.run_status = False
            self.e_stop_status = True
            
            #abruptly shutdown the main loop thread.
            #in the main machine config, setup all the i/o to render safe the machine.
            #self.main_machine_thread.stop()
            _logger.warn("Conveyor has entered the E-STOP state.")
        pass
    
    def e_stop_reset(self):
        if self.e_stop_status:
            self.run_status = False
            self.e_stop_status = False
            
            #re-boot the main loop thread
            #self.main_machine_thread.start()
            _logger.warn("Conveyor has reset the E-STOP state.")
        pass
    
class Diverter(object):
    def __init__(self):
        self.busy = False
        
        #dict of lanes this diverter is connected to for status polling
        self.lanes = {}
        
        #this dict contains the methods to call for each lane to destination lanes.
        #the key to the dict is the current lane id, the value is a dict of destination keys and value methods to call.
        #{0:{'work': method_to_call,},}
        self.lane_diverter = {}
        self.conveyor = None
        pass
    
    def divert(self, current_lane, destination_lane):
        #wait for destination lane status to be true
        while self.lanes[destination_lane].get_status():
            time.sleep(10)
            
        
        #call the method stored in the lane_diverter for this path
        self.lane_diverter[current_lane][destination_lane]()
        
        #wait for diverter clearance.
        return self.diverter_clear()
        
        
    def diverter_clear(self):
        #to be inherited by the parent class for actual clearance method.
        #this method returns True when the diverter has finished passing a carrer to the next machne.
        #returns False if there is an error
        
        time.sleep(5)
        return True