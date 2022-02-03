from odoo_automation import machine
import time, threading
import digitalio, board

class Dispenser(machine.Machine):
    def __init__(self, api, config):
        asset_id = config["equipment_id"]
        super(Dispenser, self).__init__(api, asset_id, config)
        
        #internal vars
        self.run_status = False
        self.ready_status = False
        
        self.e_stop_status = False
        self.e_stop_input = False
        self.machine_busy = False
        self.machine_warn = False
        
        self.units_name = config["units"]
        self.units_sec = config['units_sec']
        self.uom_id = self.get_uom_id(self.units_name)
        
        self.dispense_thread = threading.Thread()
        
        pass
    
    def _set_ready(self, ready_state):
        
        if self.ready_status != ready_state:
            self.ready_status = ready_state
            
            if ready_state:
                self._logger.info("Entered Ready state")
            if not ready_state:
                self._logger.info("Entered Not Ready state")
        pass
    
    def _set_busy(self, busy_state):
        if self.machine_busy != busy_state:
            self.machine_busy = busy_state
            
            if busy_state:
                self._logger.info("Entered Busy state")
            if not busy_state:
                self._logger.info("Entered Not Busy state")
        pass
    
    def _set_estop(self, estop_state):
        if self.e_stop_input != estop_state:
            self.e_stop_input = estop_state
            
            if self.e_stop_input:
                self.set_e_stop()
            
            if not self.e_stop_input:
                self.reset_e_stop()
        pass
    
    def set_e_stop(self):
        self.e_stop_status = True
        self._logger.warn("Entered E-STOP State")
        pass
    
    def reset_e_stop(self):
        self.e_stop_status = False
        self._logger.info("Reset E-STOP State")
        pass
    
    def _start_dispense(self):
        self._logger.info("Starting Dispense")
        self.run_status = True
        return True
        
    def _end_dispense(self):
        self._logger.info("Finishing Dispense")
        self.run_status = False
        return True
    
    def _dispense(self, quantity):
        self._logger.info("Dispensing %s %s(s) of material, in %s seconds" % (quantity, self.config['units'], quantity / float(self.config['units_sec']) ) )
        start = self._start_dispense()
        
        time.sleep(quantity / float(self.config['units_sec']))
        
        stop = self._end_dispense()
        return start & stop
    
    def dispense(self, quantity, wait=False):
        if self.e_stop_status:
            raise Exception("Cannot dispense while machine is in E-STOP state")
        
        if not self.ready_status:
            raise Exception("Cannot dispense while machine is not ready")
        
        if self.machine_busy:
            raise Exception("Cannot dispense while machine is currently dispensing")
            
        #spin up dispense in new thread
        self.dispense_thread = threading.Thread(target=self._dispense, args=(quantity,), daemon=True)
        self.dispense_thread.start()
        
        #if blocking flag set, wait for dispense to compleete
        if wait:
            self.wait_for_dispense()
        pass
    
    def wait_for_dispense(self):
        if self.dispense_thread.is_alive():
            self.dispense_thread.join()
        pass
    
    def quit(self):
        self._end_dispense()
        self.run_status = False
        self.ready_status = False
        return super(Dispenser, self).quit()

class FRC_advantage_ii(Dispenser):
    def __init__(self, api, config):
        super(FRC_advantage_ii, self).__init__(api, config)
        
        #FRC Advantage Vars
        self.alert_status = False
        self.material_a_low = False
        self.material_b_low = False
        self.max_program = 15
        pass
    
    def _set_material_a_low(self, material_a_low):
        
        if self.material_a_low != material_a_low:
            self.material_a_low = material_a_low
            
            if material_a_low:
                self._logger.info("Material A is low")
            if not material_a_low:
                self._logger.info("Material A is normal")
        pass
    
    def _set_material_b_low(self, material_b_low):
        
        if self.material_b_low != material_b_low:
            self.material_b_low = material_b_low
            
            if material_b_low:
                self._logger.info("Material B is low")
            if not material_b_low:
                self._logger.info("Material B is normal")
        pass
    
    def _start_dispense(self):
        return super(FRC_advantage_ii, self)._start_dispense()
        
    def _end_dispense(self):
        return super(FRC_advantage_ii, self)._end_dispense()
        
    def _dispense(self, quantity):
        return super(FRC_advantage_ii, self)._dispense(quantity)
    
    def dispense(self, quantity, wait=False):
        return super(FRC_advantage_ii, self).dispense(quantity, wait)
    
    def set_program(self, program_number):
        if program_number > self.max_program:
            raise ValueError(f"Program must be less than {self.max_program}")
            
        self._logger.info(f"Setting program to {program_number}")
        return True
        
    @property
    def pressure_a(self):
        return 0.0
        
    @property
    def pressure_b(self):
        return 0.0
        
    def quit(self):
        return super(FRC_advantage_ii, self).quit()