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
        self.workcenter_id = self.equipment_id.workcenter_id
        
        self.run_status = False
        self.e_stop_status = False
        self.busy = False
        self.warn = False
        self.indicator_start_loop = threading.Thread(target=self.indicator_start_loop, daemon=True)
        self.indicator_start_loop.start()
        self.indicator_e_stop_loop = threading.Thread(target=self.indicator_e_stop_loop, daemon=True)
        self.indicator_e_stop_loop.start()
        self.indicator_warn_loop = threading.Thread(target=self.indicator_warn_loop, daemon=True)
        self.indicator_warn_loop.start()
        return 
    
    #Button inputs
    def button_start(self):
        #if e-stop engaged, do not enter start state.
        if self.e_stop_status:
            return False
        self.run_status = True
        return True
    
    def button_stop(self):
        #if the machine is busy, wait, then stop.
        while self.busy:
            time.sleep(0.5)
            
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
        if not result:
            
            #if equipment not blocked, check work center blocking state
            if self.workcenter_id.working_state == 'blocked':
                result = True
        return result
    
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
    me.get_blocking_status()
    pass