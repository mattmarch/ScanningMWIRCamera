from PyQt5.QtCore import pyqtSignal, QThread
from ScanDataStruct import ScanData

class Scan2DThread(QThread):

    progress = pyqtSignal(int)
    return_data = pyqtSignal(ScanData)

    def __init__(self, step, start, scan_range, camera):
        QThread.__init__(self)
        self.step = step
        self.start_pos = start
        self.scan_range = scan_range
        self.camera = camera

    def abort(self):
        self.camera.end_flag = True

    def run(self):
        # ensure flag is set to False (fixes problems with QProgressDialog exiting)
        self.camera.end_flag = False
        data = self.camera.scan_image(self.start_pos, self.scan_range, self.step, display_time=False,
                                    gui_prog=self.progress)
        if data is not None:
            self.return_data.emit(data)

class Scan1DThread(QThread):

    return_data = pyqtSignal(ScanData)
