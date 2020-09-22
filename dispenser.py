import machine
import time, threading
import digitalio, board

class Dispenser(machine.Machine):
    def __init__(self):
        self.dispense_thread = threading.Thread()
        pass
        #return super(Dispenser, self).__init__()
        
    def _start_dispense(self):
        return True
        
    def _end_dispense(self):
        return True
    
    def wait_for_dispense(self):
        self.dispense_thread.join()
        pass

class FRC_advantage_ii(Dispenser):
    def __init__(self):
        self.trigger_output = object
        
        self.grams_sec = 20.0
        return super(FRC_advantage_ii, self).__init__()
        
    def _start_dispense(self):
        self.trigger_output.value = True
        return super(FRC_advantage_ii, self)._start_dispense()
        
    def _end_dispense(self):
        self.trigger_output.value = False
        return super(FRC_advantage_ii, self)._end_dispense()
        
    def _dispense(self, quantity):
        self._start_dispense()
        time.sleep(quantity / self.grams_sec)
        self._end_dispense()
        pass
    
    def dispense(self, quantity, blocking=False):
        self.dispense_thread = threading.Thread(target=self._dispense, args=(quantity,), daemon=True)
        self.dispense_thread.start()
        if blocking:
            self.dispense_thread.join()
        pass