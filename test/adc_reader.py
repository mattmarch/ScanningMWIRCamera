import sys, time
sys.path.insert(0, '..')

from lib.AdcController import *

# initialise
a = AdcController()

# open connection
a.open()

while True:
    # print reading
    print(a.read_channel())
    # sleep 50ms
    time.sleep(0.05)
