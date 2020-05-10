import machine
import logging, odoorpc, threading, time

#setup logger
_logger = logging.getLogger("Automation")

indicator_on_time = 1.0
indicator_off_time = 0.50

class Machine(machine.Machine):
    #this class is for the manufacturing automation machine
    #inherits [machine] for equpiment level functions and calibrations
    def __init__(self, api, asset_id):
        super(Machine, self).__init__(api, asset_id)
        
        #odoo route node
        self.route_node_id = None
        self.route_node_working_lane = None
        self.route_node_bypass_lane = None
        self.route_destination_cashe = {}
        self.route_node_working_queue = None
        
        self.route_node_thread = threading.Thread(target=self.route_node_updater, daemon=True)
        self.route_node_thread.start()
        self.route_queue_thread = threading.Thread(target=self.update_queues_thread, daemon=True)
        self.route_queue_thread.start()
        
        #internal vars
        self.run_status = False
        self.e_stop_status = False
        self.busy = False
        self.warn = False
        
        #indicator theads
        self.indicator_start_thread = threading.Thread(target=self.indicator_start_loop, daemon=True)
        self.indicator_start_thread.start()
        self.indicator_e_stop_thread = threading.Thread(target=self.indicator_e_stop_loop, daemon=True)
        self.indicator_e_stop_thread.start()
        self.indicator_warn_thread = threading.Thread(target=self.indicator_warn_loop, daemon=True)
        self.indicator_warn_thread.start()
        self.main_machine_thread = threading.Thread(target=self.main_machine_loop, daemon=True)
        self.main_machine_thread.start()
        _logger.info("Machine INIT Compleete.")
        return 
    
    #odoo interface
    def route_node_updater(self):
        obj_route_node = self.api.env['product.carrier.route.node']
        obj_route_node_lane = self.api.env["product.carrier.route.lane"]
        while True:
            try:
                search_domain = [('equipment_id',"=", self.equipment_id.id)]
                route_node_id = obj_route_node.browse(obj_route_node.search(search_domain, limit=1))[0]
            
                # if self.route_node_id <> route_node_id:
                #     #the node has changed, wipe out cache
                
                #set the machines Route Node    
                self.route_node_id = route_node_id
                
                self.route_node_working_lane = obj_route_node_lane.browse(obj_route_node_lane.search([("node_id", "=", self.route_node_id.id), ("type", "=", "work")]))
                self.route_node_bypass_lane = obj_route_node_lane.browse(obj_route_node_lane.search([("node_id", "=", self.route_node_id.id), ("type", "=", "bypass")]))
                
            except Exception as e:
                _logger.error(e)
            #sleep and re-casch the route node id, monitor the db for changes.
            time.sleep(60*60)
            
    def update_queues_thread(self):
        time.sleep(10)
        #loop forever
        while True:
            #refresh the queues only when running
            while self.run_status and not self.busy:
                try:
                    self.update_working_lane_queue()
                except Exception as e:
                    _logger.error(e)
                
                
                #pause time between queue refreshes
                time.sleep(5)
                
            #pause time between run_status=False refreshes
            time.sleep(1)
        
    def update_working_lane_queue(self):
        #fetch the carrier queue from the database
        obj_carrier_history = self.api.env["product.carrier.history"]
        search_doamin = [("route_node_lane_id","=",self.route_node_working_lane.id)]
        carrier_history_ids = obj_carrier_history.search(search_doamin)
        self.route_node_working_queue = obj_carrier_history.browse(carrier_history_ids)
        pass
    
    #Button inputs
    def button_start(self):
        if not self.run_status:
            #if e-stop engaged, do not enter start state.
            if self.e_stop_status:
                return False
            self.run_status = True
            
            #update the working queue
            self.update_working_lane_queue()
            
            _logger.info("Machine has entered the RUN state.")
        return True
    
    def button_stop(self):
        if self.run_status:
            #if the machine is busy, wait, then stop.
            while self.busy:
                time.sleep(0.5)
                
            self.run_status = False
            _logger.info("Machine has entered the STOPPED state.")
            return True
    
    def e_stop(self):
        #this will loop constantly while the e-stop is depressed.
        if not self.e_stop_status:
            self.run_status = False
            self.e_stop_status = True
            
            #abruptly shutdown the main loop thread.
            #in the main machine config, setup all the i/o to render safe the machine.
            #self.main_machine_thread.stop()
            _logger.warn("Machine has entered the E-STOP state.")
        pass
    
    def e_stop_reset(self):
        if self.e_stop_status:
            self.run_status = False
            self.e_stop_status = False
            
            #re-boot the main loop thread
            #self.main_machine_thread.start()
            _logger.warn("Machine has reset the E-STOP state.")
        pass
    
    #indicator outputs
    def indicator_start_loop(self):
        #main loop 
        while True:
            if not self.e_stop_status:
                if self.run_status:
                    self.indicator_start(True)
                    time.sleep(.5)
                else:
                    self.indicator_start(False)
                    time.sleep(indicator_off_time)
                    self.indicator_start(True)
                    time.sleep(indicator_on_time)
            else:
                self.indicator_start(False)
                time.sleep(.5)
                
    def indicator_start(self, value):
        #to be inherited by machine specific code
        pass
    
    def indicator_warn_loop(self):
        while True:
            if self.warn:
                self.indicator_warn(True)
            else:
                self.indicator_warn(False)
            time.sleep(1.0)    
                
    def indicator_warn(self, value):
        #to be inherited by machine specific code
        pass
    
    def indicator_e_stop_loop(self):
        #main loop 
        while True:
            if self.e_stop_status:
                self.indicator_e_stop(True)
            else:
                self.indicator_e_stop(False)
            time.sleep(.75)
                
    def indicator_e_stop(self, value):
        #to be inherited by machine specific code
        pass
            
    #machine functions
    def get_blocking_status(self):
        #pull equipment blocking state
        result = super(Machine, self).get_blocking_status()
        # if not result:
        #     #if equipment not blocked, check work center blocking state
        #     if self.workcenter_id.working_state == 'blocked':
        #         result = True
        return result
        
    def main_machine_loop(self):
        #this will be the loop the machine takes for each manufacturing cycle.
        while True:
            #this part of the loop will run only when the machine run_status = True
            while self.run_status:
                #preflight checks
                if not self.preflight_checks():
                    time.sleep(1)
                    self.warn=True
                    break
                
                #reset any warning indicator
                self.warn = False
                
                #monitor and wait for the ingress trigger.
                if not self.ingress_trigger():
                    #no product is waiting for this machine.
                    self.busy = False
                    
                    #throttle checking of the ingress trigger
                    time.sleep(1)
                    #exit this loop and start again.
                    break
                
                #we have a product to work on, set the busy flag.
                _logger.info("Machines ingress has been triggered.")
                self.busy = True
                
                #check the blocking status of the machine and workcenter in odoo.
                if self.get_blocking_status():
                    #throttle retries a bit
                    time.sleep(1)
                    #exit this loop
                    
                    _logger.warning("Machine or Workcenter is blocking this machine from running")
                    break
                
                #all is well, we can continue to bring in the product to the machine
                _logger.info("Machine is ready to process ingress")
                
                #prcess ingress, bring the product into the machine and prepare it for processing.
                if not self.process_ingress():
                    #there was a problem processing the ingress, set the run status to False and warning to True
                    self.run_status = False
                    self.warn = True
                    _logger.warning("Failed to process ingress.")
                    break
                    
                #ingress has been processed sucessfully, continue to process the product.
                _logger.info("Machine has processed ingress")
                
                
                _logger.info("Machine is ready to process egress")
                if not self.process_egress():
                    #there was a problem processing the egress, set the run status to False and warning to True
                    self.run_status = False
                    self.warn = True
                    _logger.warning("Failed to process egress.")
                    break
                _logger.info("Machine has processed egress")
            
            #throttle cpu useage when run status is False
            time.sleep(1)
                
    def preflight_checks(self):
        #to be inherited by the main machine config and returns True when the machine is ready to accept a product.
        
        #check that the machine in front of this machine is capible of accepting more product
        return False 
                
    def ingress_trigger(self):
        #to be inherited by the main machine config and returns True when the product has arrived at the ingress gate.
        return False
    
    def process_ingress(self):
        #to be inherited by the main machine config and returns True when the product has processed through ingress and is ready for processing.
        return False
        
    def process_egress(self):
        #to be inherited by the main machine config and returns True when the product has processed through egress and is clear of this machine.
        return False