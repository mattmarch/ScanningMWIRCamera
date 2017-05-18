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
