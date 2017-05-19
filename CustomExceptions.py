class MotorControllerError(Exception):
# Unexpected behaviour of motor stage controller
    pass

class MotorControllerInvalidCommandError(Exception):
# Invalid command sent via GPIB
    pass

class ImageDimensionError(Exception):
    # raised if invalid input into image dimensions
    pass

class AdcError(Exception):
# Covering any problems with the ADC controller
    pass
