import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.PWM as PWM
import logging, time, threading

import digitalio #blinka library

class stepper(object):
    def __init__(self, name, driver):
        
        #motor name and logger setup
        self.name = name
        self._logger = logging.getLogger(self.name)
        
        #driver controls the pins for the stepper
        self.driver = driver
        
        #position and speeds
        self.distance_uom = "mm"
        self.step_uom = 0.0
        self.current_uom = 0.0
        self.speed = 0.0
        
        #home and end stops
        self.pin_home = False #blinka pin object
        self.pin_end = False #blinka pin object
        
    def move_rel(self, num_uom, speed=-1):
        
        total_steps=num_uom/self.step_uom
        
        if speed < 0:
            speed = self.speed
            
        self.driver.move_steps(total_steps, speed)
        self.current_uom += num_uom
        self._logger.debug("Moving REL %s %s" % (num_uom, self.distance_uom))
        
    def move_abs(self, num_uom, speed=-1):
        delta_uom = num_uom - self.current_uom
        self._logger.debug("Moving to ABS %s %s" (num_uom, self.distance_uom))
        self.move_rel(delta_uom, speed)
    
    def home(self, blocking=False):
        if self.pin_home:
            self._logger.debug("%s - Homing" % (self.name))
            escape_max = 10
            escape_counter = 0
            self.driver.enable()
            
            for home_mode in self.config['home']['settings']['home_sequence']:
                #step away from home, if home already
                if not GPIO.input(self.pin_home):   
                    self.driver.move_steps(self.config['home']['settings']['init_step_away'] ,abs(home_mode))
                    
                #start to move in homing direction
                self.driver.move_duration(home_mode)
                
                #wait for home senor trigger 
                while GPIO.input(self.pin_home) == True:
                    pass
                
                #home sensor trggered, record the time
                time_to_home= self.driver.stop()
                self._logger.info("Home operation %s took %s seconds" % (home_mode,time_to_home))
                #move to an offset value 
                self.driver.move_steps(self.config['home']['settings']['offset'] ,abs(home_mode))
            
            #zero out the registers
            self.zero()
            
            self._logger.info("%s - Home" % (self.name))
        return True
        
    def zero(self):
        current_uom = 0.0
        pass
        
    def quit(self):
        self.driver.quit()
        self._logger.debug("Shutdown")
        
class A4988_PWM(object):
    
    def __init__(self, config):
        
        self.config = config
        self.name = self.config['name']
        self._logger = logging.getLogger(self.name)
        self.pins_direction = self.config['gpio_mux']['pin_dir']['channel']
        self.pins_step = self.config['gpio_mux']['pin_step']['channel']
        self.pins_enable = self.config['gpio_mux']['pin_enable']['channel']
        self.move_duration_start = time.ctime()
        #self.mode_pins = (config['gpio_mux']['pin_ms1']['channel'],config['gpio_mux']['pin_ms2']['channel'],config['gpio_mux']['pin_ms3']['channel']) 

        #setup GPIO Pins
        for pin in self.config['gpio_mux']:
            mux = self.config['gpio_mux'][pin]['mux']
            if mux == "GPIO":
                channel = self.config['gpio_mux'][pin]['channel']
                direction = self.config['gpio_mux'][pin]['direction']
                pullup = self.config['gpio_mux'][pin]['pullup']
                initial = self.config['gpio_mux'][pin]['initial']
                delay = self.config['gpio_mux'][pin]['delay']
            
                try:
                    GPIO.setup(channel,direction,pullup,initial,delay)
                    self._logger.debug("Set GPIO %s/%s/%s" % (pin,channel,direction) )
                except Exception as e:
                    self._logger.error("Could not set GPIO %s/%s/%s - %s" % (pin,channel,direction,e))
    
    def move_duration(self, pwm_frequency, duration=-1.0):
        self._logger.debug("Moving at %s steps/sec for %s seconds" % (pwm_frequency, duration))
        
        #set the direction based on frequencey
        self.set_direction(pwm_frequency)
        #record the time stamp, for duration return
        self.move_duration_start = time.time()
        PWM.start(self.pins_step, 50, abs(pwm_frequency))
        
        if duration > 0:
            time.sleep(duration)
            PWM.stop(self.pins_step)
            return duration
        pass
    
    def stop(self):
        PWM.stop(self.pins_step)
        duration = time.time() - self.move_duration_start
        return duration
            
    def move_steps(self, num_steps, pwm_frequency):
        self._logger.debug("Moving %s at %s steps/sec" % (num_steps, pwm_frequency))
        #do math and run motor pwm
        self.set_direction(num_steps)
        
        #calculate the time in mS it will take to step num steps at PWM frequency
        time_to_sleep = abs(num_steps) / pwm_frequency
        
        
        PWM.start(self.pins_step, 50, pwm_frequency)
        time.sleep(time_to_sleep)
        PWM.stop(self.pins_step)
        return True
    
    def set_direction(self, num):
        #set the direction output based on (+/-) number of steps
        if num > 0:
            GPIO.output(self.pins_direction, False)
        if num < 0:
            GPIO.output(self.pins_direction, True)
            
    def resolution_set(self, steptype):
        """ method to calculate step resolution
        based on motor type and steptype"""
        
        resolution = {'Full': (0, 0, 0),
                      'Half': (1, 0, 0),
                      '1/4': (0, 1, 0),
                      '1/8': (1, 1, 0),
                      '1/16': (1, 1, 1)}
                      
        multiplier = {'Full': 1.0,
                      'Half': 0.5,
                      '1/4': 0.25,
                      '1/8': 0.125,
                      '1/16': 0.0625}
                      
        if steptype in resolution:
            try:
                #GPIO.output(self.mode_pins, resolution[steptype])
                self.resolution = steptype
                self.resolution_multiplier = multiplier[steptype]
                return True
            except Exception as motor_error:
                self._logger.debug(self.name + " - Set resolution error : " + motor_error.message)
                return False
        else:
            return False
                
    def enable(self):
        return GPIO.output(self.pins_enable, False)
    
    def disable(self):
        return GPIO.output(self.pins_enable, True)
        
    def quit(self):
        self.disable()
        PWM.stop(self.pins_step)

class A4988_GPIO(object):
    def __init__(self):
        pass
    
    def stop(self):
        return duration
            
    def move(self, num_steps, frequency):
        return True
        
    def set_direction(self, num)
        pass
    
    def resolution_set(self, steptype):
        pass
    
    def enable(self):
        pass
    
    def disable(self):
        pass
    
    def quit(self):
        self.disable()

if __name__ == "__main__":
    driver = A4988_GPIO()
    
    motor = stepper("Test Motor", driver)
    