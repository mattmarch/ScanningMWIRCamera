from PyQt5.QtCore import pyqtSignal, QThread
from ScanDataStruct import ScanData
from CustomExceptions import *
import types

import time

def camera_exception_handler(func):
    def wrapped_scan_thread(self):
        try:
            func(self)
        except ImageDimensionError as e:
            # catch invalid inputs
            self.error_passback.emit(e, 'Invalid settings for image dimensions.\nSee "Show Details" for info.')
    return wrapped_scan_thread


class Scan2DThread(QThread):

    progress = pyqtSignal(int)
    return_data = pyqtSignal(ScanData)
    error_passback = pyqtSignal(Exception, str)

    def __init__(self, step, start, scan_range, camera):
        QThread.__init__(self)
        self.step = step
        self.start_pos = start
        self.scan_range = scan_range
        self.camera = camera

    def abort(self):
        self.camera.end_flag = True

    @camera_exception_handler
    def run(self):
        # ensure flag is set to False (fixes problems with QProgressDialog exiting)
        self.camera.end_flag = False
        data = self.camera.scan_image(self.start_pos, self.scan_range, self.step, display_time=False,
                                    gui_prog=self.progress)
        if data is not None:
            self.return_data.emit(data)

class Scan1DThread(QThread):

    return_data = pyqtSignal(ScanData)
    error_passback = pyqtSignal(Exception, str)

    def __init__(self, axis, other_axis_pos, step, start, scan_range, camera):
        QThread.__init__(self)
        self.axis = axis
        self.other_axis_pos = other_axis_pos
        self.step = step
        self.start_pos = start
        self.scan_range = scan_range
        self.camera = camera

    def abort(self):
        self.camera.end_flag = True

    @camera_exception_handler
    def run(self):
        self.camera.end_flag = False
        data = self.camera.scan_row(self.axis, self.other_axis_pos, self.start_pos, self.scan_range, self.step)
        if data is not None:
            self.return_data.emit(data)
