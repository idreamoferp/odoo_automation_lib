import automation
import logging, odoorpc, threading, time
import digitalio, board #blinka libs

#setup logger
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
_logger = logging.getLogger("Test Machine")

class TestMachine(automation.Machine):
    
    def __init__(self, api, asset_id):
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
        
        super(TestMachine, self).__init__(api, asset_id)
        
        self.button_input_thread = threading.Thread(target=self.button_input_loop, daemon=True)
        self.button_input_thread.start()
        
        
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
        
    
    
    #main loop functions
    def preflight_checks(self):
        #check that the machine is ready to accept a product.
        if not self.ingress_end_stop.value:
            _logger.warn("Carrier End Stop trigger, a carrier may be trapped in the machine.")
            return False
        
        return True
        
    def ingress_trigger(self):
        return not self.input_ingress.value
        
    def process_ingress(self):
        
        #open ingress gate
        self.output_ingress_gate.value = False
        _logger.info("Machine opened ingress gate, waiting for product to trigger end stop")
        
        #wait for ingress end stop trigger
        time_out = time.time()
        while self.ingress_end_stop.value:
            if time_out + 60 < time.time():
                _logger.warn("Timeout waiting for ingress end stop trigger")
                return False
            #throttle wait peroid.
            time.sleep(0.5)
        
        _logger.info("Product triggered endstop, closing ingress gate, capture product carrier")    
        self.output_ingress_gate.value = True
        self.output_carrier_capture.value = False
        
        _logger.info("Rotate the product until the carrier home is triggered")
        time.sleep(3)
        
        
        
        return True
        
        
    def process_egress(self):
        _logger.info("Machine opening egress gate, waiting to clear end stop trigger.")
        #release carrier capture
        self.output_carrier_capture.value = True
        
        #wait for egress end stop trigger
        time_out = time.time()
        while not self.ingress_end_stop.value:
            if time_out + 60 < time.time():
                _logger.warn("Timeout waiting for egress end stop trigger")
                return False
            #throttle wait peroid.
            time.sleep(0.5)
        
        return True
        
        
#startup this machine
if __name__ == "__main__":
    
    #odoo api settings, TODO: move these to a server_config file
    server = "esg-beta.idreamoferp.com"
    port = 8012
    database = "ESG_Beta_1-0"
    user_id = "justin.mangini@esg.global"
    password = "ESGmaint0719"
    
    #create instance of odooRPC clinet with these settings
    odoo = odoorpc.ODOO(server, port=port)
    
    #attempt a login to odoo server to init the api
    try:
        odoo.login(database, user_id, password)
    except Exception as e:
        _logger.error("Error logging in to odoo server",e)
    
    #asset id from odoo's maintenance.equipment model space
    odoo_equipment_asset_id = 11519
    
    #create instance of this test machine, and start its engine
    test_machine = TestMachine(api=odoo, asset_id=odoo_equipment_asset_id)
    
    while True:
        time.sleep(1000)