import random, math
import time

DATA_PREFIX = 'fake'

import visa
from CustomExceptions import *

class MotorController:
    # Initialisation
    def __init__(self):
        # empty variables show connection is not yet established
        self.instrument = None
        self.position = [None, None]

    # open connection to instrument
    def open_instrument(self):
        self.instrument = 1
        self.test_instrument_connection()
        self.init_positions()

    # test connection to instrument, allow several attempts as errors may occur after connection established.
    def test_instrument_connection(self, attempts=5):
        # check connection has been established previously
        if self.instrument is None:
            raise MotorControllerError('Must connect controller before connection can be tested.')

    # close connection safely
    def close(self):
        pass

    # move axis by given distance (in mm)
    def move(self, axis, distance):
        pass

    # send axis to endstop (positive for max, negative for min), resets position to 0
    def goto_endstop(self, axis, end):
        # check sign of end
        if end == 0:
            raise ValueError('Parameter "end" in "goto_endstop" must not be positive or negative (not 0).')
        try:
            end_sign = (end>0) - (end<0)
        except ValueError:
            raise ValueError('Parameter "end" in "goto_endstop" must not be type int or float.')
        # move past end (thus stop at endstop)
        self.move(axis, end_sign*60)
        # if self._check_endstop(axis) != end_sign:
        #     raise MotorControllerError('Did not reach endstop when expected.')
        self.position[axis] = 0

    def init_positions(self):
        self.goto_endstop(0, -1)
        self.goto_endstop(1, -1)

    # move to absolute position relative to object's reference
    def move_absolute(self, axis, to_position):
            distance = to_position - self.position[axis]
            self.move(axis, distance)

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
