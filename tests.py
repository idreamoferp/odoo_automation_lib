import automation, conveyor
import logging, odoorpc, threading, time, argparse
import digitalio, board #blinka libs
<<<<<<< HEAD
import json
from flask import Flask, render_template
=======
from flask import Flask, render_template
import json

>>>>>>> d5f749dfa1146570b30185c8f86476cf0aac4e2b
#setup logger
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s - %(message)s",datefmt='%m/%d/%Y %I:%M:%S %p',level=logging.INFO)
_logger = logging.getLogger("Test Machine")
#setup flask
app = Flask(__name__)
test_machine = False

#setup flask
app = Flask(__name__)
test_machine = False

class TestMachine(automation.MRP_Automation):
    
    def __init__(self, api, asset_id):
        #init conveyor for this machine
        self.conveyor_1 = Conveyor_1()
        
        #setup button pins
        self.button_start_input = digitalio.DigitalInOut(board.P9_12)
        self.button_start_input.direction = digitalio.Direction.INPUT
        self.button_start_input.pull = digitalio.Pull.UP
        
        self.button_stop_input = digitalio.DigitalInOut(board.P9_11)
        self.button_stop_input.direction = digitalio.Direction.INPUT
        self.button_stop_input.pull = digitalio.Pull.UP
        
        self.button_estop_input = digitalio.DigitalInOut(board.P9_15)
        self.button_estop_input.direction = digitalio.Direction.INPUT
        self.button_estop_input.pull = digitalio.Pull.UP
        
        self.button_start_led = digitalio.DigitalInOut(board.P9_14)
        self.button_start_led.direction = digitalio.Direction.OUTPUT
        self.button_start_led.value = True
        
        self.button_warn_led = digitalio.DigitalInOut(board.P9_13)
        self.button_warn_led.direction = digitalio.Direction.OUTPUT
        self.button_warn_led.value = True
        
        self.button_estop_led = digitalio.DigitalInOut(board.P9_16)
        self.button_estop_led.direction = digitalio.Direction.OUTPUT
        self.button_estop_led.value = True
        
        super(TestMachine, self).__init__(api, asset_id)
        
        self.button_input_thread = threading.Thread(target=self.button_input_loop, daemon=True)
        self.button_input_thread.start()
        
        #init route lanes
        
        self.route_lanes = [MRP_Carrier_Lane_0(self.api, self), MRP_Carrier_Lane_1(self.api, self)]
        
        _logger.info("Machine INIT Compleete.")
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
        self.button_start_led.value = not value
        return super(TestMachine, self).indicator_start(value)
    
    def indicator_warn(self, value):
        self.button_warn_led.value = not value
        return super(TestMachine, self).indicator_warn(value)
        
    def indicator_e_stop(self, value):
        self.button_estop_led.value = not value
        return super(TestMachine, self).indicator_e_stop(value)
        
    
    #Button inputs
    def button_start(self):
        return super(TestMachine, self).button_start()
    
    def button_stop(self):
        return super(TestMachine, self).button_stop()
    
    def e_stop(self):
        #put render safe i/o here.
        return super(TestMachine, self).e_stop()
    
    def e_stop_reset(self):
        #put reboot i/o here
        return super(TestMachine, self).e_stop_reset()
        
class MRP_Carrier_Lane_0(automation.MRP_Carrier_Lane):
    def __init__(self, api, mrp_automation_machine):
        
        super(MRP_Carrier_Lane_0, self).__init__(api, mrp_automation_machine)
        self._logger = logging.getLogger("Carrier Lane 0")
        
        self._logger.info("Setup GPIO Pins")
        self.input_ingress = digitalio.DigitalInOut(board.P9_17)
        self.input_ingress.direction = digitalio.Direction.INPUT
        self.input_ingress.pull = digitalio.Pull.UP
        
        self.ingress_end_stop = digitalio.DigitalInOut(board.P9_21)
        self.ingress_end_stop.direction = digitalio.Direction.INPUT
        self.ingress_end_stop.pull = digitalio.Pull.UP
        
        self.output_ingress_gate = digitalio.DigitalInOut(board.P9_18)
        self.output_ingress_gate.direction = digitalio.Direction.OUTPUT
        self.output_ingress_gate.value = True
        
        self.output_carrier_capture = digitalio.DigitalInOut(board.P9_22)
        self.output_carrier_capture.direction = digitalio.Direction.OUTPUT
        self.output_carrier_capture.value = True
        pass
    
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
        self.output_ingress_gate.value = False
        self._logger.info("Machine opened ingress gate, waiting for product to trigger end stop")
        
        #wait for ingress end stop trigger
        time_out = time.time()
        while self.ingress_end_stop.value:
            if time_out + 60 < time.time():
                self._logger.warn("Timeout waiting for ingress end stop trigger")
                return False
            #throttle wait peroid.
            time.sleep(0.5)
        
        self._logger.info("Product triggered endstop, closing ingress gate, capture product carrier")    
        self.output_ingress_gate.value = True
        self.output_carrier_capture.value = False
        
        self._logger.info("Rotate the product until the carrier home is triggered")
        time.sleep(3)
        
        
        
        return True
        
    def process_egress(self):
        self._logger.info("Machine opening egress gate, waiting to clear end stop trigger.")
        
        #configure diverter for the destination
        destination_lane = self.currernt_carrier.carrier_history_id.route_node_lane_dest_id
        self.mrp_automation_machine.conveyor_1.diverter.divert(self.route_node_lane, destination_lane)
        
        #release carrier capture
        self.output_carrier_capture.value = True
        
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
        return True
    
class MRP_Carrier_Lane_1(automation.MRP_Carrier_Lane):
    def __init__(self, api, mrp_automation_machine):
        super(MRP_Carrier_Lane_1, self).__init__(api, mrp_automation_machine)
        self._logger = logging.getLogger("Carrier Lane 1")
        pass

class Conveyor_1(conveyor.Conveyor):
    def __init__(self):
        super(Conveyor_1, self).__init__()
        self.diverter = conveyor.Diverter()
        self.diverter.lane_diverter = {'work':{'work':self.diverter_work_work,'bypass':self.diverter_work_bypass},'bypass':{'work':self.diverter_bypass_work,'bypass':self.diverter_bypass_bypass}}
        pass
    
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

<<<<<<< HEAD
#startup this machine
if __name__ == "__main__":
    
    #odoo api settings, TODO: move these to a server_config file
    server = "esg-beta.idreamoferp.com"
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
        _logger.error("Error logging in to odoo server",e)

    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--equipment-id', type=int, help='ODOO Maintence Equipment ID')
    args = parser.parse_args()
    
    #create instance of this test machine, and start its engine
    test_machine = TestMachine(api=odoo, asset_id=args.equipment_id)
    
    #start webserver
    app.run(debug=True, host='0.0.0.0', port=int("5000"))
    
    #while True:
    #    time.sleep(1000)
    exit(0)

=======
>>>>>>> d5f749dfa1146570b30185c8f86476cf0aac4e2b
@app.route("/")
def index():
   
    return render_template('index.html', machine=test_machine)
        
@app.route("/machine_vars")
def machine_vars():
    var={}
    var['run_status'] = test_machine.run_status
    var['e_stop_status'] = test_machine.e_stop_status
    var['busy'] = test_machine.busy
    var['warn'] = test_machine.warn
    return json.dumps(var)
    
@app.route("/route_node")
def route_node():
    var={}
    var['route_lanes'] = test_machine.route_lanes
    var['route_node_id'] = {}
    if test_machine.route_node_id:
        var['route_node_id']['id'] = test_machine.route_node_id.id
        var['route_node_id']['name'] = test_machine.route_node_id.name
        
<<<<<<< HEAD
    return json.dumps(var)
=======
    return json.dumps(var)
    
#startup this machine
if __name__ == "__main__":
    
    #odoo api settings, TODO: move these to a server_config file
    server = "esg-beta.idreamoferp.com"
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
        _logger.error("Error logging in to odoo server",e)
    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--equipment-id', type=int, help='ODOO Maintence Equipment ID')
    args = parser.parse_args()
    
    #create instance of this test machine, and start its engine
    test_machine = TestMachine(api=odoo, asset_id=args.equipment_id)
    
    #launch web service
    app.run(debug=True, host='0.0.0.0', port=int("5000"))
    pass

>>>>>>> d5f749dfa1146570b30185c8f86476cf0aac4e2b
