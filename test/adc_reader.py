import sys, os, time
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

from AdcController import *

# initialise
a = AdcController()

# open connection
a.open()

while True:
    # print reading
    print(a.read_channel())
    # sleep 50ms
    time.sleep(0.05)
