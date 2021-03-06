import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))
from MotorController import *

to_x = float(sys.argv[1])
to_y = float(sys.argv[2])

print('Moving to ({}, {})'.format(to_x, to_y))

m = MotorController()

m.open_instrument()

m.move_absolute(0, to_x)
m.move_absolute(1, to_y)

m.close()
