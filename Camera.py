import numpy
import pickle
import time
import os, sys
from dateutil.relativedelta import relativedelta

sys.path.insert(0, './lib')

# from FakeControllers import *       # for testing without using equipment
from MotorController import *
from AdcController import *

from ScanDataStruct import ScanData
from CustomExceptions import ImageDimensionError

import numpy as np
from matplotlib import pyplot as plt

# to check if image exceeds the limits of the stepper array
IMAGE_LIMITS = ((0, 50), (0, 50))

# decorator to initialise controllers at start and end of calls
def initialise_controllers(func):
    def wrapped_function(self, *args, **kwargs):
        # test motor controller connection
        try:
            self.motors.test_instrument_connection()
        except MotorControllerError:
            self.motors.open_instrument()
        # connect to adc
        self.adc.open()
        result = func(self, *args, **kwargs)
        self.adc.close()
        return result
    return wrapped_function

class Camera:
    # Initialisation
    def __init__(self, reset_positions=True):
        self.motors = MotorController()
        self.adc = AdcController()
        self.SAMPLING_FUNC = 'rms'
        self.N_SAMPLES = 5
        self.end_flag = False

    # Scan Image where arguments: start_pos, img_size and pixel_size are all 2 element tuples or lists
    @initialise_controllers
    def scan_image(self, start_pos, img_size, pixel_size,
                    display_time=True, gui_prog=None):
        self.check2dDimensions(start_pos, img_size, pixel_size)
        # move axis 0 to start
        self.motors.move_absolute(0, start_pos[0])
        # scan over range
        pixel_array = []
        scan_range = int(img_size[0]/pixel_size[0])
        # for time remaining
        if display_time:
            start_time = time.time()
        for i in range(scan_range):
            row = self._scan_axis(1, start_pos[1], img_size[1], pixel_size[1])
            # handle aborted scan
            if row is None:
                return None
            else:
                pixel_array += [row]
            self.motors.move(0, pixel_size[0])
            if display_time and i > 0:
                # calculate time remaining
                fraction_complete = i/scan_range
                elapsed_time = time.time() - start_time
                t_remaining = relativedelta(seconds=round((1/fraction_complete - 1) * elapsed_time))
                print('{perc}% complete: {t_m}m, {t_s}s remaining.'.format(perc=round(fraction_complete*100, 2),
                                                            t_m=t_remaining.minutes, t_s=t_remaining.seconds))
            # update gui progress bar (don't update if exiting)
            if gui_prog is not None and not self.end_flag:
                gui_prog.emit(i)
        # return data object
        return ScanData(pixel_size, start_pos, img_size, pixel_array, time.time())


    # Scan row
    @initialise_controllers
    def scan_row(self, axis, other_axis_pos, start_pos, scan_range, step_size):
        self.check1dDimensions(axis, other_axis_pos, start_pos, scan_range, step_size)
        # move other axis to start
        if other_axis_pos is not None:
            self.motors.move_absolute(int(not axis), other_axis_pos)
        # scan row and plot output
        data = self._scan_axis(axis, start_pos, scan_range, step_size)
        if data is None:
            return None
        else:
            return ScanData(step_size, start_pos, scan_range, data, time.time(), axis, other_axis_pos)

    # Close communication with motors
    def close(self):
        self.motors.close()

    # Plot data stored in 'last_image_backup'
    def plot_backup(self, start=(0,0), step=(0,0)):
        with open('last_image_backup', 'rb') as f:
            data = pickle.load(f)
        self._plot_row(data, start, step)

    def set_sampling_variables(self, samples, samplefunc):
        self.N_SAMPLES = samples
        self.SAMPLING_FUNC = samplefunc


    # Scan along an axis and return list of values
    def _scan_axis(self, axis, start_pos, scan_range, step_size):
        data = []
        # move to start
        self.motors.move_absolute(axis, start_pos)
        # read first value
        data.append(self.adc.read(self.N_SAMPLES, self.SAMPLING_FUNC))
        # iterate over rest of values moving then adding value to the list
        for i in range(int(scan_range/step_size)):
            self.motors.move(axis, step_size)
            data.append(self.adc.read(self.N_SAMPLES, self.SAMPLING_FUNC))
            # abort scan
            if self.end_flag:
                self.end_flag = False
                return None
        return data

    # Plot a row given a list of data
    def _plot_row(self, data, start, step):
        x_vals = np.arange(start, start+step*len(data), step)
        plt.plot(x_vals, data)
        plt.xlabel('Position (mm)')
        plt.ylabel('Relative intensity')
        plt.show()

    def _plot_2d(self, data, start, step):
        # data transposed to show horizontal on x axis
        plt.imshow(data, interpolation='nearest', cmap='inferno',
                extent=[start[0], start[0]+step[0]*len(data[0]), start[1], start[1]+step[1]*len(data)])
        plt.show()

    def check2dDimensions(self, start, img_size, step):
        img_end = (start[0]+img_size[0], start[1]+img_size[1])
        # check step is positive
        if step[0] <= 0 or step[1] <= 0:
            raise ImageDimensionError('Both step sizes (set to ({}, {})) must be > 0'.format(
                step[0], step[1]))
        # check positive image sizes
        elif img_size[0] <= 0 or img_size[1] <= 0:
            raise ImageDimensionError('Both image dimensions (set to ({}, {}) must be > 0)'.format(
                img_size[0], img_size[1]))
        # check step greater than image size
        elif step[0] > img_size[0] or step[1] > img_size[1]:
            raise ImageDimensionError('Step sizes (set to ({}, {})) must be less than image dimensions ({}, {})'.format(
                step[0], step[1], img_size[0], img_size[1]))
        # check start positions
        elif start[0] < IMAGE_LIMITS[0][0] or start[0] > IMAGE_LIMITS[0][1]:
            raise ImageDimensionError('x start position (set to {}) must be in range {} to {}'.format(
                start[0], IMAGE_LIMITS[0][0], IMAGE_LIMITS[0][1]))
        elif start[1] < IMAGE_LIMITS[1][0] or start[1] > IMAGE_LIMITS[1][1]:
            raise ImageDimensionError('y start position (set to {}) must be in range {} to {}'.format(
                start[1], IMAGE_LIMITS[1][0], IMAGE_LIMITS[1][1]))
        # check end positions
        elif img_end[0] < IMAGE_LIMITS[0][0] or img_end[0] > IMAGE_LIMITS[0][1]:
            raise ImageDimensionError('x end (currently at {} + {} = {}) must be in range {} to {}'.format(
                start[0], img_size[0], img_end[0], IMAGE_LIMITS[0][0], IMAGE_LIMITS[0][1]))
        elif img_end[1] < IMAGE_LIMITS[1][0] or img_end[1] > IMAGE_LIMITS[1][1]:
            raise ImageDimensionError('y end (currently at {} + {} = {}) must be in range {} to {}'.format(
                start[1], img_size[1], img_end[1], IMAGE_LIMITS[1][0], IMAGE_LIMITS[1][1]))

    def check1dDimensions(self, axis, other_axis_pos, start, img_size, step):
        img_end = start + img_size
        other_axis = 0 if axis else 1
        axis_names = ('x', 'y')
        # check step is positive
        if step <= 0:
            raise ImageDimensionError('Step size (set to {}) must be > 0'.format(step))
        # check positive image sizes
        elif img_size <= 0:
            raise ImageDimensionError('Scan dimension (set to {}) must be > 0)'.format(img_size))
        # check step greater than image size
        elif step > img_size:
            raise ImageDimensionError('Step size (set to {}) must be less than scan range ({})'.format(
                step, img_size))
        # check other axis is within range
        elif other_axis_pos < IMAGE_LIMITS[other_axis][0] or other_axis_pos > IMAGE_LIMITS[other_axis][1]:
            raise ImageDimensionError('{} position must be in range {} to {}'.format(
                axis_names[other_axis], IMAGE_LIMITS[other_axis][0], IMAGE_LIMITS[other_axis][1]))
        # check start position
        elif start < IMAGE_LIMITS[axis][0] or start > IMAGE_LIMITS[axis][1]:
            raise ImageDimensionError('Start position (set to {}) must be in range {} to {}'.format(
                start, IMAGE_LIMITS[axis][0], IMAGE_LIMITS[axis][1]))
        # check end position
        elif img_end < IMAGE_LIMITS[axis][0] or img_end > IMAGE_LIMITS[axis][1]:
            raise ImageDimensionError('End position (currently at {} + {} = {}) must be in range {} to {}'.format(
                start, img_size, img_end, IMAGE_LIMITS[axis][0], IMAGE_LIMITS[axis][1]))

if __name__ == '__main__':
    c = Camera()
    # c.scan_row(1, 29.3, 20, 30, 0.1)
    c.scan_image((27,34), (4,3), (0.25,0.25))
