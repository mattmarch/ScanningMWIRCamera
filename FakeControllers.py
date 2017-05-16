import random, math
import time

DATA_PREFIX = 'fake'

class MotorControllerError(Exception):
# Unexpected behaviour of motor stage controller
    pass

class MotorControllerInvalidCommandError(Exception):
# Invalid command sent via GPIB
    pass


class MotorController:
    # Initialisation
    def __init__(self):
        self.position = [0, 0]

    # close connection safely
    def close(self):
        pass

    # move axis by given distance (in mm)
    def move(self, axis, distance):
        self.position[axis] += distance
        # time.sleep(0.000001)

    # send axis to endstop (positive for max, negative for min), resets position to 0
    def goto_endstop(self, axis, end):
        self.position[axis] = 0

    # move to absolute position relative to object's reference
    def move_absolute(self, axis, to_position):
        self.position[axis] = to_position
        time.sleep(0.02)


class AdcError(Exception):
# Covering any problems with the ADC controller
    pass

class AdcController():

    # initialise process
    def __init__(self):
        pass
        # will need to start subprocess when not running simple control.

    def open(self):
        pass

    def close(self):
        pass
        # kill subprocess

    # read samples in from ADC and apply func to find value to return
    def read(self, n, func='max'):
        # take samples
        samples = []
        for i in range(n):
            samples += [self._get_val()]
        # apply chosen func
        if func == 'max':
            # choose maximum value
            return max(samples)
        elif func == 'average':
            # average values
            return sum(samples)/n
        elif func == 'rms2':
            # mean square of values
            samples_sq = [s*s for s in samples]
            return sum(samples_sq)/n
        elif func == 'rms':
            samples_sq = [s*s for s in samples]
            return math.sqrt(sum(samples_sq)/n)
        elif func == 'sum':
            # sum of values
            return sum(samples)
        else:
            raise ValueError('"{}" not valid value for "func" in AdcControl.read'.format(func))

    def _get_val(self):
        # get output, decode to regular string and strip whitespace characters
        return random.randint(0,100)
