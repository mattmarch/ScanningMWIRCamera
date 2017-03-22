import subprocess
import math

class AdcError(Exception):
# Covering any problems with the ADC controller
    pass

class AdcController():
    ADC_PROCESS_SIMPLE = 'ADC/adc_control_simple.exe'
    ADC_PROCESS = None

    # initialise process
    def __init__(self):
        pass
        # will need to start subprocess when not running simple control.

    def close(self):
        pass
        # kill subprocess

    def test(self):
        while True:
            print(self._get_val_simple())

    # read samples in from ADC and apply func to find value to return
    def read(self, n, func='max'):
        # take samples
        samples = []
        for i in range(n):
            samples += [self._get_val()]
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

    def _get_val_simple(self):
        # get output, decode to regular string and strip whitespace characters
        output = subprocess.check_output(self.ADC_PROCESS_SIMPLE).decode().strip()
        # check output is of form "Val: 00"
        try:
            if output[0:3] == 'Val':
                return int(output[5:])
            else:
                raise ValueError
        except (IndexError, ValueError):
            raise AdcError('Unexpected response from ADC_PROCESS_SIMPLE, received "{}"'.format(output))

    def _get_val(self):
        return self._get_val_simple()
