from lib.AdcController import *
import time

# initialise
a = AdcController()

# open connection
a.open()

while True:
    # print reading
    print(a.read_channel())
    # sleep 50ms
    time.sleep(0.05)
