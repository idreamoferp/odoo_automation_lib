import logging, odoorpc, threading, time
_logger = logging.getLogger("ODOO")

class workcenter_machine(machine):
    #this class is for the manufacturing automation machine
    #inherits [machine] for equpiment level functions and calibrations
    def __init__(self):
        return super(workcenter_machine, self).__init__()
    
class machine(object):
    def __init__(self):
        pass