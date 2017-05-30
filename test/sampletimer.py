# Simple script to determine the length of time it takes to perform a sample using the ADC
import sys, os, time
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from Camera import *


# time over 1000 samples
n = 1000

a = AdcController()

a.open()

t1 = time.time()

for i in range(n):
    a.read_channel()

t2 = time.time()

dt = t2-t1
print('{} read_channel calls:'.format(n))
print('Total: {}, Per read: {}'.format(dt, dt/n))
