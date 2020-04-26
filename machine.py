
import logging, odoorpc, threading, time

#setup logger
_logger = logging.getLogger("Machine")

class Machine(object):
    def __init__(self, api, asset_id):
        self.api = api
        self.asset_id = asset_id
        self.equipment_id = self.api.env['maintenance.equipment'].browse(asset_id)
        _logger.info("Machine INIT Compleete.")
        return
    
    def get_blocking_status(self):
        #not yet implemented in odoo, return false to indicate the machine is not blocked from running
        return False
        
    