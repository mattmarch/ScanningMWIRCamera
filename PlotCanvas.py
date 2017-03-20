from PyQt5.QtWidgets import QSizePolicy

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot

import numpy
from collections import OrderedDict

class PlotCanvas(FigureCanvas):

    INTERPOLATIONS = OrderedDict([
        ('Nearest'              ,   'nearest'),
        ('Linear'               ,   'bilinear'),
        ('Cubic'                ,   'bicubic'),
        ('Sinc'                 ,   'sinc')
    ])
    CMAPS = OrderedDict([
        ('Inferno'              ,   'inferno'),
        ('Heat 1'               ,   'gist_heat'),
        ('Grayscale'            ,   'gray'),
        ('Heat 2'               ,   'hot'),
        ('Grayscale Reversed'   ,   'Greys')
    ])


    def __init__(self, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width,height), dpi=dpi)
        self.axis = self.fig.add_subplot(111)

        # function None when nothing to show on plot.
        self.draw_plot_func = None

        self.show_initial_figure()

        FigureCanvas.__init__(self, self.fig)

        # set to interactive mode (supresses event loop message)
        pyplot.ion()

        # connect mouse click
        self.fig.canvas.mpl_connect('button_press_event', self.clicked)

        # set figure sizing properties
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


    def clicked(self, event):
        if self.draw_plot_func != None:
            self.draw_plot_func()
            if self.plot_axis == None:
                pyplot.xlabel('x position (mm)')
                pyplot.ylabel('y position (mm)')
            else:
                pyplot.xlabel('{} position (mm)'.format(self.plot_axis))
                pyplot.ylabel('Intensity')
            pyplot.show()

    def show_initial_figure(self):
        pass

    def update_plot_2d(self, data, interp, cmap):
        self.axis.grid(False)
        imshow_args = {'X': numpy.transpose(data.data), 'interpolation': self.INTERPOLATIONS[interp], 'cmap': self.CMAPS[cmap],
                'extent': [data.start[0], data.start[0]+data.scan_range[0], data.start[1]+data.scan_range[1], data.start[1]]}
        self.axis.imshow(**imshow_args)
        self.draw()
        # create function for showing figure in interactive window
        self.draw_plot_func = lambda: pyplot.imshow(**imshow_args)
        # indicate 2d
        self.plot_axis = None

    def update_plot_1d(self, data):
        self.axis.cla()
        self.axis.set_aspect('auto')
        self.axis.grid(True)
        plot_args = [numpy.arange(data.start, data.start+data.scan_range+data.step, data.step), data.data]
        # TODO: fix this hack work out why lists end up different lengths!
        plot_args[0] = plot_args[0][:len(plot_args[1])]
        self.axis.plot(*plot_args)
        self.draw()
        self.draw_plot_func = lambda: pyplot.plot(*plot_args)
        self.plot_axis = 'y' if data.scan_axis else 'x'
