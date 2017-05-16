import math
import ctypes

ADC_CHANNEL_USED = 1        # 1 or 2

class AdcError(Exception):
# Covering any problems with the ADC controller
    pass

class AdcController():

    # initialise process
    def __init__(self):
        ADC_DLL = ctypes.WinDLL('K8055D.dll')
        # create dll functions for use
        self.f_search = ADC_DLL.SearchDevices
        self.f_open = ADC_DLL.OpenDevice
        self.read_channel = lambda: ADC_DLL.ReadAnalogChannel(ADC_CHANNEL_USED)
        self.close = ADC_DLL.CloseDevice

    def open(self):
        # TODO: use search to find board if not in 0
        if self.f_open(0) == -1:
            raise AdcError('Connection to board unsuccessful.')

    # read samples in from ADC and apply func to find value to return
    def read(self, n, func='max'):
        # take samples
        samples = []
        for i in range(n):
            samples += [self.read_channel()]
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
