import visa
from CustomExceptions import MotorControllerInvalidCommandError, MotorControllerError, MotorControllerConnectionError

class MotorController:
    # Initialisation
    def __init__(self):
        self.rm = visa.ResourceManager()
        # empty variables show connection is not yet established
        self.instrument = None
        self.position = [None, None]

    # open connection to instrument
    def open_instrument(self):
        expected_device_name = 'GPIB0::6::INSTR'
        connected_devices = self.rm.list_resources()
        if expected_device_name in connected_devices:
            device_name = expected_device_name
        else:
            # try connecting to first connected device
            # will work if device name is changed and only one instrument is connected to computer
            try:
                device_name = connected_devices[0]
                # connect to first device but print a warning to console
                print('Warning: expected address for motor controller ({}) not found, instead connnecting to {}'.format(
                    expected_device_name, device_name))
            except IndexError:
                raise MotorControllerConnectionError('No connected devices found while initialising MotorController connection.')
        self.instrument = self.rm.open_resource(device_name, timeout=6000)
        self.test_instrument_connection()
        self.init_positions()

    # test connection to instrument, allow several attempts as errors may occur after connection established.
    def test_instrument_connection(self, attempts=5):
        # check connection has been established previously
        if self.instrument is None:
            raise MotorControllerError('Must connect controller before connection can be tested.')

        EXPECTED_RESULT = 'MELLES GRIOT NANOSTEP'
        for i in range(attempts):
            test_result = self._query('*IDN?')
            if test_result == EXPECTED_RESULT:
                break
        else:
            # all 5 attempts unsuccessful
            # disconnect instrument
            self.instrument = None
            # raise error
            raise MotorControllerError('"*IDN?" not returning expected result. Expected "{expected}", received "{received}"'.format(expected=EXPECTED_RESULT, received=test_result))

    # close connection safely
    def close(self):
        if self.instrument is not None:
            self.instrument.close()
            self.instrument = None

    # move axis by given distance (in mm)
    def move(self, axis, distance, uncalibrated=False):
        if distance != 0:
            self._query('MR{a}={d}'.format(a=axis, d=distance))
            if not uncalibrated:
                self.position[axis] += distance

    # send axis to endstop (positive for max, negative for min), resets position to 0
    def goto_endstop(self, axis, end):
        # check sign of end
        if end == 0:
            raise ValueError('Parameter "end" in "goto_endstop" must not be positive or negative (not 0).')
        try:
            end_sign = (end>0) - (end<0)
        except ValueError:
            raise ValueError('Parameter "end" in "goto_endstop" must not be type int or float.')
        # move past end (thus stop at endstop)
        self.move(axis, end_sign*60, True)
        if self._check_endstop(axis) != end_sign:
            raise MotorControllerError('Did not reach endstop when expected.')
        self.position[axis] = 0

    def init_positions(self):
        self.goto_endstop(0, -1)
        self.goto_endstop(1, -1)

    # move to absolute position relative to object's reference
    def move_absolute(self, axis, to_position):
            distance = to_position - self.position[axis]
            self.move(axis, distance)

    # Send a query via GPIB, returns response or raises MotorControllerInvalidCommandError if error returned
    def _query(self, message):
        try:
            response = self.instrument.query(message)
            if response == 'E':
                raise MotorControllerInvalidCommandError('Invalid Command: "{}"'.format(message))
            else:
                return response
        except VisaIOError:
            # timeout
            # reset connection next time use is needed
            self.instrument = None
            raise


    # returns -1 if at axis min, 1 if at axis max, else 0
    def _check_endstop(self, axis):
        result = self._query('?L{}'.format(axis))
        if result == '11':
            # disconnect instrument
            self.instrument = None
            raise MotorControllerError('Both endstops triggered, this should be impossible.')
        try:
            return int(result[0]) - int(result[1])
        except (ValueError, IndexError):
            raise MotorControllerError('Erroneously received {} on endstop check'.format(result))

    # FOLLOWING METHODS ARE NOT USED (AT LEAST YET)

    # get absolute position from motor controller
    def get_position(self, axis):
        pos = self._query('?P{}'.format(axis))

    # move to absolute position relative to controller's reference
    def move_controller_absolute(self, axis, to_position):
        self.position[axis] += to_position - self.get_position(axis)
        self._query('MA{a}={p}'.format(a=axis, p=position))

    # datum axis on controller
    def _datum_axis(self, axis):
        self._query('D{}'.format(axis))
