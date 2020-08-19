import machine
import logging, threading, time

#setup logger
_logger = logging.getLogger("Automation")

indicator_on_time = 1.0
indicator_off_time = 0.50

class MRP_Automation(machine.Machine):
    #this class is for the manufacturing automation machine
    #inherits [machine] for equpiment level functions and calibrations
    def __init__(self, api, asset_id):
        super(MRP_Automation, self).__init__(api, asset_id)

        #odoo route node
        self.route_node_id = False
        self.route_node_thread = threading.Thread(target=self.update_route_node_loop, daemon=True)
        self.route_node_thread.start()
        self.route_lanes = []
        
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

        _logger.info("MRP Automation INIT Complete.")
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
        for i in range(len(self.route_node_id.lane_ids)):
            #set the lane_id on the lane objects stored in list self.route_lanes
            self.route_lanes[i].route_node_lane = self.route_node_id.lane_ids[i]
            pass

        _logger.info("Updated Route Node Lanes")
        pass

    #Button inputs
    def button_start(self):
        #if the run status is already True, skip these things.
        if not self.run_status:

            if self.e_stop_status:
                #the machine is in an e-stop status, cannot start.
                return False

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
        result = super(MRP_Automation, self).get_blocking_status()
        # if not result:
        #     #if equipment not blocked, check work center blocking state
        #     if self.workcenter_id.working_state == 'blocked':
        #         result = True
        return result

    def quit(self):
        _logger.info("Machine Shutdown.")
        return super(MRP_Automation, self).quit()   

class MRP_Carrier_Lane(object):
    def __init__(self, api, mrp_automation_machine):
        #upper level machine vars
        self.api = api
        self.mrp_automation_machine = mrp_automation_machine

        self.busy = False #busy flag to indicate this lane is in the process of doing work.
        self.warn = False #warning flag to indicate this lane has a warning

        #route node lanes
        self.route_node_lane = False

        #carrier lane queue for this lane
        self.carrier_history_cache = {} #this var contains the carrier history database objects that are in the queue
        self.route_node_carrier_queue = [] #this var contains the order the carriers are in the queue by history_id
        self.currernt_carrier = False #this is the carrier currently in the machine to be worked on.

        self.route_queue_thread = threading.Thread(target=self.update_queues_thread, daemon=True)
        self.route_queue_thread.start()

        #main worker thread
        self.main_machine_thread = threading.Thread(target=self.main_machine_loop, daemon=True)
        self.main_machine_thread.start()
        
        _logger.info("MRP Automation Lane INIT Complete.")
        pass

    #upper level machine vars
    @property
    def run_status(self):
        return self.mrp_automation_machine.run_status

    @property
    def e_stop_status(self):
        return self.mrp_automation_machine.e_stop_status

    @property
    def warn(self):
        return self.mrp_automation_machine.warn

    @warn.setter
    def warn(self, value):
        self.mrp_automation_machine.warn = value

    #Lane queueing and updating.
    def update_queues_thread(self):
        time.sleep(10)
        #loop forever
        while True:
            #refresh the queues only when running

            while self.run_status and not self.busy and self.route_node_lane:
                try:
                    self.update_lane_queue()
                except Exception as e:
                    self._logger.error(e)

                #pause time between queue refreshes
                time.sleep(5)

            #pause time between run_status=False refreshes
            time.sleep(1)

    def update_lane_queue(self):
        self._logger.debug("Updateing Carrier Queue")

        #fetch the carrier_ids queue from the database
        obj_carrier_history = self.api.env["product.carrier.history"]
        search_doamin = [("route_node_lane_id","=",self.route_node_lane.id)]
        self.route_node_carrier_queue = obj_carrier_history.search(search_doamin)

        #cycle through all the carriers in the database, verify them in the queue
        for carrier_history in obj_carrier_history.browse(self.route_node_carrier_queue):
            if carrier_history.id not in self.carrier_history_cache:
                #add this carrier to the queue cache.
                self.carrier_history_cache[carrier_history.id] = Carrier(self.api, carrier_history, carrier_lane_id = self.route_node_lane)
                self._logger.info("Added to Queue - %s" % (carrier_history.display_name))

        #TODO will need to pop() out the entires in carrier_history_cache{} that are not in route_node_carrier_queue[] at some point
        pass


    #machine loop and events
    def main_machine_loop(self):
        #this will be the loop the machine takes for each manufacturing cycle.
        while True:
            #this part of the loop will run only when the machine run_status = True
            while self.run_status:
                #preflight checks
                if not self.preflight_checks():
                    self.warn=True
                    self._logger.warning("Failed Pre-Flight checks.")
                    time.sleep(30)
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
                self._logger.info("Machines ingress has been triggered.")
                self.busy = True

                #set the current carrier var
                if len(self.route_node_carrier_queue) == 0:
                    self._logger.warn("The Carrier Queue is empty.")
                    self.busy = False
                    time.sleep(10)
                    break

                self.currernt_carrier = self.carrier_history_cache[self.route_node_carrier_queue[0]]
                self._logger.info("Processing %s" % self.currernt_carrier.carrier_history_id.name)

                #check the blocking status of the machine and workcenter in odoo.
                if self.mrp_automation_machine.get_blocking_status():
                    #throttle retries a bit
                    time.sleep(1)
                    #exit this loop

                    self._logger.warning("Machine or Workcenter is blocking this machine from running.")
                    break

                #all is well, we can continue to bring in the product to the machine
                self._logger.info("Machine is ready to process ingress.")
                self.currernt_carrier.logger.info("Processing Carrier")
                #prcess ingress, bring the product into the machine and prepare it for processing.
                if not self.process_ingress():
                    #there was a problem processing the ingress, set the run status to False and warning to True
                    self.warn = True
                    self._logger.warning("Failed to process ingress.")
                    break

                #ingress has been processed sucessfully, continue to process the product.
                self._logger.info("Machine has processed ingress.")

                #process egress from the machine.
                self._logger.info("Machine is ready to process egress.")
                if not self.process_egress():
                    #there was a problem processing the egress, set the run status to False and warning to True
                    self.warn = True
                    self._logger.warning("Failed to process egress.")
                    break
                self._logger.info("Machine has processed egress.")


                #process carrier compleeted in the database
                self.currernt_carrier.carrier_history_id.transfer_carrier()
                #remove the carrier history from the cache
                self.carrier_history_cache.pop(self.currernt_carrier.id)
                self.route_node_carrier_queue.pop(0)
                #clear the current carrier var
                self.currernt_carrier = False
            time.sleep(1)

    def preflight_checks(self):
        #to be inherited by the main machine config and returns True when the machine is ready to accept a product.

        #check that the machine in front of this machine is capible of accepting more product
        return True

    def ingress_trigger(self):
        #to be inherited by the main machine config and returns True when the product has arrived at the ingress gate.
        return False

    def process_ingress(self):
        #to be inherited by the main machine config and returns True when the product has processed through ingress and is ready for processing.
        return False

    def process_egress(self):
        #to be inherited by the main machine config and returns True when the product has processed through egress and is clear of this machine.
        return False

class Carrier(object):
    def __init__(self, api, carrier_history_id, carrier_lane_id):
        self.api = api
        self.lane_id = carrier_lane_id
        self.carrier_history_id = carrier_history_id
        self.logger = logging.getLogger("%s %s" % (self.lane_id.name, carrier_history_id.barcode))

        #setup custom logger to log carrier events to carrier history in odoo
        ch = Carrier_Handler(carrier = carrier_history_id)
        ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(ch)
        self.logger.info("Create Carier")
        pass

    @property
    def id(self):
        return self.carrier_history_id.id

from logging import StreamHandler

class Carrier_Handler(StreamHandler):
    def __init__(self, carrier):
        StreamHandler.__init__(self)
        self.carrier = carrier

    def emit(self, record):
        try:
            msg = self.format(record)
            self.carrier.log_event(msg)
        except Exception as e:
            pass

        pass

