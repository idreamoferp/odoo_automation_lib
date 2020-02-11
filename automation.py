import machine
import logging, odoorpc, threading, time

#setup logger
_logger = logging.getLogger("Automation")

indicator_on_time = 2.0
indicator_off_time = 3.0

class Machine(machine.Machine):
    #this class is for the manufacturing automation machine
    #inherits [machine] for equpiment level functions and calibrations
    def __init__(self, api, asset_id):
        super(Machine, self).__init__(api, asset_id)
        self.workcenter_id = self.equipment_id.workcenter_id
        
        self.run_status = False
        self.e_stop_status = False
        self.indicator_start_loop = threading.Thread(target=self.indicator_start_loop)
        self.indicator_start_loop.start()
        self.indicator_e_stop_loop = threading.Thread(target=self.indicator_e_stop_loop)
        self.indicator_e_stop_loop.start()
        return 
    
    #Button inputs
    def button_start(self):
        if self.e_stop_status:
            return False
        self.run_status = True
        return True
    
    def button_stop(self):
        self.run_status = False
        return True
    
    def e_stop(self):
        self.run_status = False
        self.e_stop_status = True
        pass
    
    def e_stop_reset(self):
        self.run_status = False
        self.e_stop_status = False
        pass
    
    #indicator outputs
    def indicator_start_loop(self):
        #main loop 
        while True:
            if self.run_status:
                self.indicator_start(True)
                time.sleep(1)
            else:
                self.indicator_start(False)
                time.sleep(indicator_off_time)
                self.indicator_start(True)
                time.sleep(indicator_on_time)
                
    def indicator_start(self, value):
        #to be inherited by machine specific code
        pass
    
    def indicator_e_stop_loop(self):
        #main loop 
        while True:
            if self.e_stop_status:
                self.indicator_e_stop(True)
            else:
                self.indicator_e_stop(False)
            time.sleep(1)
                
    def indicator_e_stop(self, value):
        #to be inherited by machine specific code
        pass
            
    #machine functions

if __name__ == "__main__":
    server = "esg-beta.idreamoferp.com"
    port = 8012
    database = "ESG_Beta_1-0"
    user_id = "justin.mangini@esg.global"
    password = "ESGmaint0719"
    #create instance of odooRPC clinet
    odoo = odoorpc.ODOO(server, port=port)
    
    try:
        odoo.login(database, user_id, password)
    except Exception as e:
        _logger.error("Error logging in to odoo server",e)
        
    
    me = Machine(api=odoo, asset_id=5)
    pass