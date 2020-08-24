

class MotonControl():
    def __init__(self, config):
        self.config = config
        self.position_x = 0.0
        self.position_y = 0.0
        self.position_z = 0.0
        self.work_offset_x = 0.0
        self.work_offset_y = 0.0
        self.work_offset_z = 0.0
        self.actual_feedrate = 0.0
        self.actual_spindle = 0.0
        self.override_feed = 100
        self.override_rapids = 100
        self.override_spindle = 100
        self.errors = []
        
    pass

    def goto_position_abs(self,x=False,y=False,z=False,a=False,b=False,feed=False):
        self._goto_position(x,y,z,a,b,feed)
        return True
   
    def goto_position_rel(self,x=False,y=False,z=False,a=False,b=False,feed=False):
        self._goto_position(x,y,z,a,b,feed)
        return True
       
    def _goto_position(self,x=False,y=False,z=False,a=False,b=False,feed=False):
        return True
   
    def home(self):
        return True
        
    def work_offset(self,x=0,y=0,z=0,a=0,b=0):
        return True
        