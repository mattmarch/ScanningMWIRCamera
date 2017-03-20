import os, sys, datetime, csv
from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout,
                            QComboBox, QTabWidget, QDialog, QProgressDialog,
                            QFileDialog, QMenu, QMenuBar, QAction, QMainWindow,
                            QApplication)
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtGui import QIcon

# if FakeControllers is imported this is overwritten.
DATA_PREFIX = 'scan'

from PlotCanvas import *
from SettingsTabs import *
from Camera import *

# decorator to run process in background from StackOverflow http://stackoverflow.com/a/30092938
def nongui(fun):
    """Decorator running the function in non-gui thread while
    processing the gui events."""
    from multiprocessing.pool import ThreadPool

    def wrap(*args, **kwargs):
        pool = ThreadPool(processes=1)
        async = pool.apply_async(fun, args, kwargs)
        while not async.ready():
            async.wait(0.01)
            QApplication.processEvents()
        return async.get()

    return wrap

# function to get printable date from timestamp
def timetostring(time_int, forfile=False):
    string_format = '%Y/%m/%d %H:%M:%S' if not forfile else '%Y-%m-%d-%H-%M-%S'
    return datetime.datetime.fromtimestamp(int(time_int)).strftime(string_format)

# Parallel thread for 2D scan
class Scan2DThread(QThread):

    progress = pyqtSignal(int)
    return_data = pyqtSignal(ScanData)

    def __init__(self, step, start, scan_range, samples, samplefunc, camera):
        QThread.__init__(self)
        self.step = step
        self.start_pos = start
        self.scan_range = scan_range
        self.samples = samples
        self.samplefunc = samplefunc
        self.camera = camera

    def abort(self):
        self.camera.end_flag = True

    def run(self):
        data = self.camera.scan_image(self.start_pos, self.scan_range, self.step, display_time=False,
                                    gui_prog=self.progress, plot_out=False,
                                    samplefunc=self.samplefunc, n_samples=self.samples)
        if data is not None:
            self.return_data.emit(data)

class CameraGUI(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()
        self.camera = Camera()

    def initUI(self):

        # main layout
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        hBoxMain = QHBoxLayout()
        hBoxMain.addStretch(1)
        centralWidget.setLayout(hBoxMain)

        # menu bar
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        helpMenu = menuBar.addMenu('Help')
        # open file action
        openAction = QAction('&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open a saved data file.')
        openAction.triggered.connect(self.open_file)
        fileMenu.addAction(openAction)
        # save image file action
        saveAction = QAction('&Save As Image', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save current plot as image.')
        saveAction.triggered.connect(self.save_file)
        fileMenu.addAction(saveAction)
        # save csv file action
        saveCsvAction = QAction('&Save As CSV', self)
        saveCsvAction.setShortcut('Ctrl+Shift+S')
        saveCsvAction.setStatusTip('Save current data as CSV.')
        saveCsvAction.triggered.connect(self.save_csv_file)
        fileMenu.addAction(saveCsvAction)

        # plot items
        self.plot_canvas = PlotCanvas()
        self.plot_info = QLabel('No plot to display.\n\n')
        # 2d settings
        self.plot_settings_2d = QWidget()
        plot_settings_2d_layout = QHBoxLayout(self.plot_settings_2d)
        self.interpolation_control = QComboBox()
        self.interpolation_control.addItems(list(PlotCanvas.INTERPOLATIONS.keys()))
        self.interpolation_control.currentIndexChanged.connect(self.update_plot_2d)
        self.colour_control = QComboBox()
        self.colour_control.addItems(list(PlotCanvas.CMAPS.keys()))
        self.colour_control.currentIndexChanged.connect(self.update_plot_2d)
        plot_settings_2d_layout.addWidget(QLabel('Interpolation mode: '))
        plot_settings_2d_layout.addWidget(self.interpolation_control)
        plot_settings_2d_layout.addWidget(QLabel('Colour mapping: '))
        plot_settings_2d_layout.addWidget(self.colour_control)
        self.plot_settings_2d.setVisible(False)

        # vbox for plot
        vBoxPlot = QVBoxLayout()
        vBoxPlot.addStretch(1)
        vBoxPlot.addWidget(self.plot_canvas)
        vBoxPlot.addWidget(self.plot_info)
        vBoxPlot.addWidget(self.plot_settings_2d)

        # tabs for settings
        settingsTabs = QTabWidget()
        self.settings2d = SettingsTab2D(self.scan_2D)
        self.settings1d = SettingsTab1D(self.scan_1D)
        settingsTabs.addTab(self.settings2d, '2D')
        settingsTabs.addTab(self.settings1d, '1D')

        hBoxMain.addLayout(vBoxPlot)
        hBoxMain.addWidget(settingsTabs)

        self.setWindowIcon(QIcon('Res/scan_icon.png'))
        self.setGeometry(100, 100, 800, 500)
        self.setWindowTitle('MWIR Camera')
        self.show()

    def scan_2D(self, step, start, scan_range, samples, samplefunc):
        # disable button
        self.settings2d.button.setEnabled(False)
        # start progress dialog
        self.progress_dialog = QProgressDialog('2D Scan in progress.', 'Abort', 0, int(scan_range[0]/step[0])-1)
        self.progress_dialog.setWindowTitle('Scan Progress')
        self.progress_dialog.setMinimumDuration(500)
        # run scan in parallel to gui
        self.scan_thread = Scan2DThread(step, start, scan_range, samples, samplefunc, self.camera)
        self.progress_dialog.canceled.connect(self.scan_2d_canceled)
        self.scan_thread.return_data.connect(self.scan_2d_completed)
        self.scan_thread.progress.connect(self.progress_dialog.setValue)
        self.scan_thread.start()


        # if scan_output is None:
        #     print('None returned')
        #     return
        # else:
        #     self.data = scan_output
        # # close progress dialog
        # progress_dialog.close()

    def scan_2d_completed(self, data):
        self.data = data
        # show result
        self.update_plot_2d()
        # save data to file
        fileName = 'ScanData/{pre}-{t}-2d.scandat'.format(
        pre=DATA_PREFIX, t=timetostring(self.data.timestamp, True))
        with open(fileName, 'wb') as f:
            pickle.dump(self.data, f)
            # enable button
            self.settings2d.button.setEnabled(True)

    def scan_2d_canceled(self):
        self.progress_dialog.close()
        self.scan_thread.abort()
        self.settings2d.button.setEnabled(True)

    def update_plot_2d(self):
        self.plot_canvas.update_plot_2d(self.data, self.interpolation_control.currentText(),
                                        self.colour_control.currentText())
        # update plot info
        self.plot_info.setText('2D Scan taken at {time}.\n'
            'Pixel resolution {x_res}μm x {y_res}μm.\n'
            'Image size {x_range}mm x {y_range}mm.'.format(
                                                time=timetostring(self.data.timestamp),
                                                x_res=self.data.step[0]*1000, y_res=self.data.step[1]*1000,
                                                x_range=self.data.scan_range[0], y_range=self.data.scan_range[1]))
        # show 2d plot settings
        self.plot_settings_2d.setVisible(True)

    # @nongui
    # def parallel_scan_2D(self, step, start, scan_range, samples, samplefunc, progress_dialog):
    #     return self.camera.scan_image(start, scan_range, step, display_time=False,
    #                                 gui_prog=progress_dialog, plot_out=False,
    #                                 samplefunc=samplefunc, n_samples=samples)


    def scan_1D(self, axis, other_axis_pos, step, start, scan_range, samples, samplefunc):
        # disable button
        self.settings1d.button.setEnabled(False)
        # scan and update
        self.data = self.parallel_scan_1D(axis, other_axis_pos, step, start, scan_range,
                                            samples, samplefunc)
        self.update_plot_1d()
        # save data to file
        fileName = 'ScanData/{pre}-{t}-1d.scandat'.format(
                        pre=DATA_PREFIX, t=timetostring(self.data.timestamp, True))
        with open(fileName, 'wb') as f:
            pickle.dump(self.data, f)
        # enable button
        self.settings1d.button.setEnabled(True)

    def update_plot_1d(self):
        self.plot_canvas.update_plot_1d(self.data)
        # update plot info
        self.plot_info.setText('1D Scan along {axis} axis taken at {time}.\n'
            '{off_axis} axis fixed at {off_axis_pos}\n'
            'Step resolution {step}μm. Scan range {scan_range}mm.'.format(
                axis='y' if self.data.scan_axis else 'x', time=timetostring(self.data.timestamp),
                off_axis='x' if self.data.scan_axis else 'y', off_axis_pos=self.data.off_axis_pos,
                step=self.data.step*1000, scan_range=self.data.scan_range))
        # show 2d plot settings
        self.plot_settings_2d.setVisible(False)


    @nongui
    def parallel_scan_1D(self, axis, other_axis_pos, step, start, scan_range, samples, samplefunc):
        return self.camera.scan_row(axis, other_axis_pos, start, scan_range, step,
                                    samplefunc, samples, False)

    def open_file(self):
        fileName = QFileDialog.getOpenFileName(self, 'Select a data file to open.',
                                                'ScanData/', 'Scan data (*.scandat)')
        if fileName[0] == '':
            return
        with open(fileName[0], 'rb') as f:
            data = pickle.load(f)
        if type(data) is ScanData:
            self.data = data
            try:
                if data.scan_axis is not None:
                    self.update_plot_1d()
                else:
                    self.update_plot_2d()
            except NameError:
                # first scans performed don't define scan_axis (but are all 2d)
                self.update_plot_2d()
        else:
            # TODO: raise error
            pass

    def save_file(self):

        fileName = QFileDialog.getSaveFileName(self, 'Choose a location to save.',
                    'Images/image-{}'.format(timetostring(self.data.timestamp, True)),
                    'PNG Image (*.png)')
        if fileName[0] == '':
            return
        self.plot_canvas.fig.savefig(fileName[0])

    def save_csv_file(self):
        fileName = QFileDialog.getSaveFileName(self, 'Choose a location to save.',
                    'Data/data-{}'.format(timetostring(self.data.timestamp, True)),
                    'CSV File (*.csv)')
        if fileName[0] == '':
            return
        with open(fileName[0], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(self.data.data)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CameraGUI()
    sys.exit(app.exec_())
