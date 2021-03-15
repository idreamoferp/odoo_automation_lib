
import logging, odoorpc, threading, time, atexit

#setup logger
_logger = logging.getLogger("Machine")

class Machine(object):
    def __init__(self, api, asset_id, config):
         #sets an on exit function
        atexit.register(self.quit)
        
        self.api = api
        self.asset_id = asset_id
        self.equipment_id = False 
        if self.asset_id:
            self.equipment_id = self.api.env['maintenance.equipment'].browse(asset_id)
        
        _logger.info("Machine INIT Compleete.")
        return
    @property
    def name(self):
        if self.equipment_id:
            return self.equipment_id.name
            
    def get_blocking_status(self):
        #not yet implemented in odoo, return false to indicate the machine is not blocked from running
        return False
        
    def quit(self):
        _logger.info("Machine Shutdown.")
        pass
        
    
        
    