import machine
import logging, odoorpc, threading, time

#setup logger
_logger = logging.getLogger("Automation")

indicator_on_time = 1.0
indicator_off_time = 0.50

class MRP_Automation(machine.Machine):
    #this class is for the manufacturing automation machine
    #inherits [machine] for equpiment level functions and calibrations
    def __init__(self, api, asset_id):
        super(Machine, self).__init__(api, asset_id)
        
        #odoo route node
        self.route_node_id = False
        self.route_node_working_lane = False
        self.route_node_bypass_lane = False
        
        #route node lanes
        self.route_node_working_queue = [] #this var contains the order the carriers are in the queue by history_id
        self.route_node_bypass_queue = [] #this var contains the order the carriers are in the queue by history_id
        self.route_node_thread = threading.Thread(target=self.update_route_node_loop, daemon=True)
        self.route_node_thread.start()
        self.route_queue_thread = threading.Thread(target=self.update_queues_thread, daemon=True)
        
        self.carrier_history_cache = {} #this var contains the carrier history database objects that are in the queue
        self.currernt_carrier = False
        
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
    
    #odoo carrer route methods
    def update_route_node_loop(self):
        search_domain = [('equipment_id',"=", self.equipment_id.id)]
        
        while True:
            try:
                #festch the route node assigned to this equipment from the database
                route_node_id = self.api.env['product.carrier.route.node'].search(search_domain, limit=1)[0]
                
                if not self.route_node_id:
                    #this is the first pass, set the route node up
                    self.update_route_node(route_node_id)
                    
                if self.route_node_id.id != route_node_id:
                    #the route node has changed in the database, re-setup the route node
                    self.update_route_node(route_node_id)
            except Exception as e:

                _logger.error("There was an error fetching the route node %s" % (e))
            
            #sleep and re-casch the route node id, monitor the db for changes.
            time.sleep(60*60)
            
    def update_route_node(self, route_node_id):
        #the node has changed, wipe out cache
        self.carrier_history_cache ={}
        self.route_destination_cashe = {}
        
        #set the machines Route Node    
        self.route_node_id = self.api.env['product.carrier.route.node'].browse(route_node_id)
        
        #setup the lanes on this route node
        for lane in self.route_node_id.lane_ids:
            #setup the working lane
            if lane.type =="work" and not self.route_node_working_lane:
                self.route_node_working_lane = lane
                
            #setup the bypass lane
            if lane.type == "bypass" and not self.route_node_bypass_lane:
                self.route_node_bypass_lane = lane
        
        #start the queue thread
        self.route_queue_thread.start()
        pass
            
    def update_queues_thread(self):
        time.sleep(10)
        #loop forever
        while True:
            #refresh the queues only when running
            while self.run_status and not self.busy and self.route_node_id:
                try:
                    self.update_working_lane_queue()
                except Exception as e:
                    _logger.error(e)
                
                
                #pause time between queue refreshes
                time.sleep(5)
                
            #pause time between run_status=False refreshes
            time.sleep(1)
        
    def update_working_lane_queue(self):
        _logger.info("Updateing carrier Queue")
        
        self.route_node_working_queue = []
        self.route_node_bypass_queue = []
        
        #fetch the carrier_ids queue from the database
        obj_carrier_history = self.api.env["product.carrier.history"]
        search_doamin = [("route_node_lane_id.node_id","=",self.route_node_id.id)]
        carriers = obj_carrier_history.browse(obj_carrier_history.search(search_doamin))
        
        #cycle through all the carriers in the database, verify them in the queue
        for carrier_history in carriers:
            if carrier_history.route_node_lane_id.type == 'work':
                self.route_node_working_queue.append(carrier_history.id)
                
            if carrier_history.route_node_lane_id.type == 'bypass':
                self.route_node_bypass_queue.append(carrier_history.id)
                
            if carrier_history.id not in self.carrier_history_cache:
                #add this carrier to the queue cache.
                self.carrier_history_cache[carrier_history.id] = Carrier(self.api, carrier_history)
        pass
    
    #Button inputs
    def button_start(self):
        #if the run status is already True, skip these things.
        if not self.run_status:
            
            if self.e_stop_status:
                #the machine is in an e-stop status, cannot start.
                return False
                
            #update the working queue
            self.update_working_lane_queue()
            
            #set the run status to True to start the machine.
            self.run_status = True
            
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
                
                #reset any preflight warning indicators
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
                
                #set the current carrier var
                
                self.currernt_carrier = self.carrier_history_cache[self.route_node_working_queue[0]]
                _logger.info("Processing %s" % self.currernt_carrier.carrier_history_id.name)
                
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
                
                #process egress from the machine.
                _logger.info("Machine is ready to process egress")
                if not self.process_egress():
                    #there was a problem processing the egress, set the run status to False and warning to True
                    self.run_status = False
                    self.warn = True
                    _logger.warning("Failed to process egress.")
                    break
                _logger.info("Machine has processed egress")
                
                
                #process carrier compleeted in the database
                self.currernt_carrier.carrier_history_id.mark_as_done()
                #remove the carrier history from the cache
                self.carrier_history_cache[self.currernt_carrier.id].pop()
                #clear the current carrier var
                self.currernt_carrier = False
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
    
    def quit(self):
        _logger.info("Machine Shutdown.")
        return super(Machine, self).quit()    
        
        
class Carrier(object):
    def __init__(self, api, carrier_history_id):
        self.api = api
        self.carrier_history_id = carrier_history_id
        
        _logger.info("Added %s" % (self.carrier_history_id.name))
        pass
    
