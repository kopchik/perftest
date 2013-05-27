#!/usr/bin/env python
from useful.bench import StopWatch
import numpy as np
import blosc
import sys

a = np.linspace(0, 100, 3e6)
bytes_array = a.tostring()

for x in range(int(sys.argv[1])):
  with StopWatch() as t:
    packed = blosc.pack_array(a)
    blosc.unpack_array(packed)
    del packed
  print("real: {0:.2f} cpu: {0:.2f}".format(t.time, t.cpu))
