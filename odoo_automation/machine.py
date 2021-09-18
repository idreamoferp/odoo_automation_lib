import logging, odoorpc, threading, time, atexit

#setup logger
_logger = logging.getLogger("Machine")

class Machine(object):
    def __init__(self, api, asset_id, config):
         #sets an on exit function
        atexit.register(self.quit)
        
        self.api = api
        self.config = config
         
        self.asset_id = int(asset_id) or False
        self.equipment_id = False 
        
        if self.asset_id:
            self.equipment_id = self.api.env['maintenance.equipment'].browse(self.asset_id)
        
        self._logger = logging.getLogger(self.name or "Machine")
        
        self._logger.info("Machine INIT Compleete.")
        return
    
    def get_uom_id(self, uom_name):
        domain = [("name", "=", uom_name)]
        uom_id = self.api.env['uom.uom'].search(domain)
        if uom_id:
            uom_id = self.api.env['uom.uom'].browse(uom_id[0])
        return uom_id
    
    @property
    def name(self):
        if self.equipment_id:
            return self.equipment_id.name
        return None
            
    def get_blocking_status(self):
        #not yet implemented in odoo, return false to indicate the machine is not blocked from running
        return False
        
    def quit(self):
        _logger.info("Machine Shutdown.")
        pass
        
    
        
    