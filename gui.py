import os, sys, datetime, csv, time
from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout,
                            QComboBox, QTabWidget, QDialog, QProgressDialog,
                            QFileDialog, QMenu, QMenuBar, QAction, QMainWindow,
                            QApplication)
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtGui import QIcon

# if FakeControllers is imported this is overwritten.
DATA_PREFIX = 'scan'

from PlotCanvas import PlotCanvas
from SettingsTabs import SettingsTab1D, SettingsTab2D
from ScanThreads import Scan2DThread, Scan1DThread
from ErrorMessage import ErrorMessage
from Camera import *

# function to get printable date from timestamp
def timetostring(time_int, forfile=False):
    string_format = '%Y/%m/%d %H:%M:%S' if not forfile else '%Y-%m-%d-%H-%M-%S'
    return datetime.datetime.fromtimestamp(int(time_int)).strftime(string_format)

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
        # menubar
        self.init_menubar()
        # plot panel
        hBoxMain.addLayout(self.init_plot_panel())
        # tabs for settings
        settingsTabs = QTabWidget()
        self.settings2d = SettingsTab2D(self.scan_2D)
        self.settings1d = SettingsTab1D(self.scan_1D)
        settingsTabs.addTab(self.settings2d, '2D')
        settingsTabs.addTab(self.settings1d, '1D')
        hBoxMain.addWidget(settingsTabs)
        # window settings
        self.setWindowIcon(QIcon('Res/scan_icon.png'))
        self.setGeometry(100, 100, 800, 500)
        self.setWindowTitle('MWIR Camera')
        self.show()

    def init_menubar(self):
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

    def init_plot_panel(self):
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
        return vBoxPlot

    def scan_2D(self, step, start, scan_range, samples, samplefunc):
        # disable button
        self.settings2d.button.setEnabled(False)
        # set camera sampling methods
        self.camera.set_sampling_variables(samples, samplefunc)
        # start progress dialog
        self.progress_dialog = QProgressDialog('2D Scan in progress.', 'Abort', 0, int(scan_range[0]/step[0])-1)
        self.progress_dialog.setWindowTitle('Scan Progress')
        self.progress_dialog.setMinimumDuration(500)
        # run scan in parallel to gui
        self.scan_thread = Scan2DThread(step, start, scan_range, self.camera)
        self.progress_dialog.canceled.connect(self.scan_2d_canceled)
        self.scan_thread.return_data.connect(self.scan_2d_completed)
        self.scan_thread.progress.connect(self.progress_dialog.setValue)
        self.scan_thread.start()

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
        self.scan_thread.abort()
        # self.progress_dialog.close()
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

    def scan_1D(self, axis, other_axis_pos, step, start, scan_range, samples, samplefunc):
        # disable button
        self.settings1d.button.setEnabled(False)
        # update sampling variables
        self.camera.set_sampling_variables(samples, samplefunc)
        # create progress bar
        self.progress_dialog = QProgressDialog('1D Scan in progress.', 'Abort', 0, 0)
        self.progress_dialog.setWindowTitle('Scan Progress')
        self.progress_dialog.setRange(0, 0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        self.scan_thread = Scan1DThread(axis, other_axis_pos, step, start, scan_range, self.camera)
        self.scan_thread.return_data.connect(self.scan_1d_completed)
        self.progress_dialog.canceled.connect(self.scan_1d_canceled)
        self.scan_thread.start()

    def scan_1d_completed(self, data):
        self.progress_dialog.close()
        self.data = data
        # show result
        self.update_plot_1d()
        # save data to file
        fileName = 'ScanData/{pre}-{t}-1d.scandat'.format(
            pre=DATA_PREFIX, t=timetostring(self.data.timestamp, True))
        with open(fileName, 'wb') as f:
            pickle.dump(self.data, f)
        # enable button
        self.settings1d.button.setEnabled(True)

    def scan_1d_canceled(self):
        self.progress_dialog.close()
        self.scan_thread.abort()
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

    def open_file(self):
        fileName = QFileDialog.getOpenFileName(self, 'Select a data file to open.',
                                                'ScanData/', 'Scan data (*.scandat)')
        if fileName[0] == '':
            return
        with open(fileName[0], 'rb') as f:
            try:
                data = pickle.load(f)
            except pickle.UnpicklingError as e:
                ErrorMessage(e, 'Could not load file. \nFile may be corrupted.')
                return
        if type(data) is ScanData:
            self.data = data
            try:
                if data.scan_axis is not None:
                    self.update_plot_1d()
                else:
                    self.update_plot_2d()
            except NameError:
                # first scans performed didn't implement scan_axis (but are all 2d)
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

    # close necessary features when app exited
    def closeEvent(self, event):
        self.camera.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CameraGUI()
    sys.exit(app.exec_())
