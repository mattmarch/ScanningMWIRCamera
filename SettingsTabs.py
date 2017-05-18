from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout,
                            QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox, QRadioButton,
                            QFrame, QPushButton, QTabWidget)


class BlankSettingsTab(QWidget):

    def __init__(self, scan_func):
        super().__init__()
        self.scan_func = scan_func
        self.vLayout = QVBoxLayout()
        self.addAxisSelect()
        self.addResolutionControl()
        self.vLayout.addWidget(HLine())
        self.addRangeControl()
        self.vLayout.addWidget(HLine())
        self.addSamplingControl()
        self.vLayout.addWidget(HLine())
        self.addButton()
        self.setLayout(self.vLayout)

    # empty methods
    def addAxisSelect(self):
        pass
    def addResolutionControl(self):
        pass
    def addRangeControl(self):
        pass
    def addButton(self):
        pass

    # sampling control
    def addSamplingControl(self):
        layout = QGridLayout()
        layout.addWidget(QLabel('Samples per point: '), 0, 0, 1, 1)
        # no. of samples select
        self.n_samples = QSpinBox()
        self.n_samples.setRange(1, 9999)
        self.n_samples.setValue(5)
        layout.addWidget(self.n_samples, 0, 1, 1, 1)

        # sampling mode select
        layout.addWidget(QLabel('Sampling function: '), 1, 0, 1, 1)
        self.sampling_mode = QComboBox()
        self.sampling_mode.addItems(['RMS', 'Squared RMS', 'Average', 'Sum', 'Max'])
        layout.addWidget(self.sampling_mode, 1, 1, 1, 1)

        self.vLayout.addLayout(layout)

    def getSamplingMethod(self):
        methods = { 'Squared RMS'   :   'rms2',
                    'RMS'           :   'rms',
                    'Average'       :   'average',
                    'Sum'           :   'sum',
                    'Max'           :   'max'}
        return methods[self.sampling_mode.currentText()]

class SettingsTab2D(BlankSettingsTab):

    def addResolutionControl(self):
        layout = QGridLayout()
        layout.addWidget(QLabel('Pixel Resolution (μm)'), 0, 0, 1, -1)

        # dx control
        self.dx_control = QSpinBox()
        self.dx_control.setRange(10, 10000)
        self.dx_control.setSingleStep(10)
        self.dx_control.setValue(100)
        layout.addWidget(QLabel('dx: '), 1, 0, 1, 1)
        layout.addWidget(self.dx_control, 1, 1, 1, 1)

        # dy control
        self.dy_control = QSpinBox()
        self.dy_control.setRange(10, 10000)
        self.dy_control.setSingleStep(10)
        self.dy_control.setValue(100)
        layout.addWidget(QLabel('dy: '), 1, 2, 1, 1)
        layout.addWidget(self.dy_control, 1, 3, 1, 1)

        # check box and action
        keep_aspect = QCheckBox('keep dy = dx')
        keep_aspect.stateChanged.connect(lambda: self.keep_aspect_state_changed(keep_aspect.checkState()))
        keep_aspect.setCheckState(True)
        keep_aspect.setTristate(False)
        layout.addWidget(keep_aspect, 2, 0, 1, -1)
        layout.setRowStretch(3, -1)

        # link dy = dx
        self.dx_control.valueChanged.connect(lambda x: self.dy_control.setValue(x) if keep_aspect.checkState() else None)
        # add to top layout
        self.vLayout.addLayout(layout)

    def keep_aspect_state_changed(self, state):
        if state:
            self.dy_control.setValue(self.dx_control.value())
        self.dy_control.setEnabled(not state)

    def addRangeControl(self):
        layout = QGridLayout()
        layout.addWidget(QLabel('Image Range (mm)'), 0, 0, 1, -1)

        # x start control
        self.x_start_control = QDoubleSpinBox()
        self.x_start_control.setRange(0, 50)
        self.x_start_control.setSingleStep(0.01)
        self.x_start_control.setValue(10)
        layout.addWidget(QLabel('x start: '), 1, 0, 1, 1)
        layout.addWidget(self.x_start_control, 1, 1, 1, 1)

        # y start control
        self.y_start_control = QDoubleSpinBox()
        self.y_start_control.setRange(0, 50)
        self.y_start_control.setSingleStep(0.01)
        self.y_start_control.setValue(10)
        layout.addWidget(QLabel('y start: '), 1, 2, 1, 1)
        layout.addWidget(self.y_start_control, 1, 3, 1, 1)

        # x range control
        self.x_range_control = QDoubleSpinBox()
        self.x_range_control.setRange(0, 50)
        self.x_range_control.setSingleStep(0.01)
        self.x_range_control.setValue(30)
        layout.addWidget(QLabel('x range: '), 2, 0, 1, 1)
        layout.addWidget(self.x_range_control, 2, 1, 1, 1)

        # y range control
        self.y_range_control = QDoubleSpinBox()
        self.y_range_control.setRange(0, 50)
        self.y_range_control.setSingleStep(0.01)
        self.y_range_control.setValue(30)
        layout.addWidget(QLabel('y range: '), 2, 2, 1, 1)
        layout.addWidget(self.y_range_control, 2, 3, 1, 1)

        layout.setRowStretch(4, -1)

        # add to top layout
        self.vLayout.addLayout(layout)

    def addButton(self):
        self.button = QPushButton('2D Scan')
        self.button.clicked.connect(lambda: self.scan_func((self.dx_control.value()/1000, self.dy_control.value()/1000),
                                                        (self.x_start_control.value(), self.y_start_control.value()),
                                                        (self.x_range_control.value(), self.y_range_control.value()),
                                                        self.n_samples.value(), self.getSamplingMethod()))
        self.vLayout.addWidget(self.button)


class SettingsTab1D(BlankSettingsTab):

    def addAxisSelect(self):
        layout = QVBoxLayout()
        # radio buttons
        button_layout = QHBoxLayout()
        self.scan_x = QRadioButton('Scan x', self)
        self.scan_y = QRadioButton('Scan y', self)
        self.scan_x.setChecked(True)
        button_layout.addWidget(self.scan_x)
        button_layout.addWidget(self.scan_y)
        layout.addLayout(button_layout)
        # other axis position select
        position_layout = QHBoxLayout()
        position_label = QLabel('y position (mm): ')
        position_layout.addWidget(position_label)
        self.other_axis_pos_control = QDoubleSpinBox()
        self.other_axis_pos_control.setRange(0, 50)
        self.other_axis_pos_control.setSingleStep(0.01)
        self.other_axis_pos_control.setValue(25)
        position_layout.addWidget(self.other_axis_pos_control)
        layout.addLayout(position_layout)
        # link radio buttons to position_label
        self.scan_x.toggled.connect(
                lambda x: position_label.setText('{} position (mm): '.format('y' if x else 'x')))
        # assemble
        self.vLayout.addLayout(layout)
        self.vLayout.addWidget(HLine())

    def addResolutionControl(self):
        layout = QHBoxLayout()
        # step control
        self.step_control = QSpinBox()
        self.step_control.setRange(10, 10000)
        self.step_control.setSingleStep(10)
        self.step_control.setValue(100)
        layout.addWidget(QLabel('Step Resolution (μm): '))
        layout.addWidget(self.step_control)

        # add to top layout
        self.vLayout.addLayout(layout)


    def addRangeControl(self):
        layout = QGridLayout()
        layout.addWidget(QLabel('Scan Range (mm)'), 0, 0, 1, -1)

        # start control
        self.start_control = QDoubleSpinBox()
        self.start_control.setRange(0, 50)
        self.start_control.setSingleStep(0.01)
        self.start_control.setValue(10)
        layout.addWidget(QLabel('Start: '), 1, 0, 1, 1)
        layout.addWidget(self.start_control, 1, 1, 1, 1)

        # range control
        self.range_control = QDoubleSpinBox()
        self.range_control.setRange(0, 50)
        self.range_control.setSingleStep(0.01)
        self.range_control.setValue(30)
        layout.addWidget(QLabel('Range: '), 2, 0, 1, 1)
        layout.addWidget(self.range_control, 2, 1, 1, 1)

        layout.setRowStretch(4, -1)

        # add to top layout
        self.vLayout.addLayout(layout)

    def addButton(self):
        self.button = QPushButton('1D Scan')
        self.button.clicked.connect(lambda: self.scan_func(int(self.scan_y.isChecked()),
                                    self.other_axis_pos_control.value(), self.step_control.value()/1000,
                                    self.start_control.value(), self.range_control.value(),
                                    self.n_samples.value(), self.getSamplingMethod()))
        self.vLayout.addWidget(self.button)


class HLine(QFrame):
    def __init__(self):
        super(HLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
