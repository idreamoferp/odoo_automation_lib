import configparser

class MotonControl(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.status = False
        self.is_home = False
        
        self.position_x = 0.0
        self.position_y = 0.0
        self.position_z = 0.0
        self.position_a = 0.0
        self.position_b = 0.0
        
        self.work_offset_x = 0.0
        self.work_offset_y = 0.0
        self.work_offset_z = 0.0
        self.work_offset_a = 0.0
        self.work_offset_b = 0.0
        pass
    
    def read_config(self, config):
        if 'motion_control' in config:
            self.config = config['motion_control']
        
        if 'motion_control' not in config:
            self.config = self.get_default_config()
        
        return True
    
    def get_default_config(self):
        return {}
        
    def write_config(self, config):
        config['motion_control'] = self.config
        return config
        
    def work_offset(self,x=0,y=0,z=0,a=0,b=0):
        self.work_offset_x = x
        self.work_offset_y = y
        self.work_offset_z = z
        self.work_offset_a = a
        self.work_offset_b = b
        pass
    
    def home(self):
        self.position_x = 0.0
        self.position_y = 0.0
        self.position_z = 0.0
        self.position_a = 0.0
        self.position_b = 0.0
        self.is_home = True
        return True
    
    def _goto_position(self,x=False,y=False,z=False,a=False,b=False,feed=False):
        pass
    
    def goto_position_rel(self,x=False,y=False,z=False,a=False,b=False,feed=False):
        self._goto_position(x+self.position_x, y+self.position_y, z+self.position_z, a+self.position_a, b+self.position_b, feed)
        pass
    
    def goto_position_abs(self,x=False,y=False,z=False,a=False,b=False,feed=False):
        self._goto_position(x+self.work_offset_x, y+self.work_offset_y, z+self.work_offset_z, a+self.work_offset_a, b+self.work_offset_b, feed)
        pass
    
    