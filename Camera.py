import numpy
import pickle
import time
from dateutil.relativedelta import relativedelta

from FakeControllers import *       # for testing without using equipment
# from MotorController import *
# from AdcController import *

import numpy as np
from matplotlib import pyplot as plt

# data structure to store info about data for GUI
class ScanData:
    def __init__(self, step, start, scan_range, data, timestamp, scan_axis=None,
                off_axis_pos=None, name=None):
        self.step = step
        self.start = start
        self.scan_range = scan_range
        self.data = data
        self.timestamp = timestamp
        self.name = name
        self.scan_axis = scan_axis
        self.off_axis_pos = off_axis_pos

class Camera:
    # Initialisation
    def __init__(self, reset_positions=True):
        self.motors = MotorController()
        self.adc = AdcController()
        self.SAMPLING_FUNC = 'rms2'
        self.N_SAMPLES = 5
        # initialise motor positions
        if reset_positions:
            self.init_positions()
        self.end_flag = False

    def init_positions(self):
        self.motors.goto_endstop(0, -1)
        self.motors.goto_endstop(1, -1)

    # Scan Image where arguments: start_pos, img_size and pixel_size are all 2 element tuples or lists
    def scan_image(self, start_pos, img_size, pixel_size, display_time=True,
                    gui_prog=None):
        # open connection with adc
        self.adc.open()
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
        # close adc Connection
        self.adc.close()
        # return data object
        return ScanData(pixel_size, start_pos, img_size, pixel_array, time.time())


    # Scan row
    def scan_row(self, axis, other_axis_pos, start_pos, scan_range, step_size):
        # move other axis to start
        if other_axis_pos is not None:
            self.motors.move_absolute(int(not axis), other_axis_pos)
        # scan row and plot output
        data = self._scan_axis(axis, start_pos, scan_range, step_size)
        return ScanData(step_size, start_pos, scan_range, data, time.time(), axis, other_axis_pos)

    # Close communication with ADC and motors
    def close(self):
        self.motors.close()
        self.adc.close()

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

if __name__ == '__main__':
    c = Camera()
    # c.scan_row(1, 29.3, 20, 30, 0.1)
    c.scan_image((27,34), (4,3), (0.25,0.25))
