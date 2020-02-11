
import logging, odoorpc, threading, time

#setup logger
_logger = logging.getLogger("Machine")

class Machine(object):
    def __init__(self, api, asset_id):
        self.api = api
        self.asset_id = asset_id
        self.equipment_id = self.api.env['maintenance.equipment'].browse(asset_id)
        pass