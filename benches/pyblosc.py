#!/usr/bin/env python
from useful.bench import StopWatch
import numpy as np
import argparse
import blosc
import sys

parser = argparse.ArgumentParser(description='Run experiments')
parser.add_argument('-r', '--repeat', '--repeats', type=int, default=100, help="number of repeats")
args = parser.parse_args()

a = np.linspace(0, 100, 3e6)
bytes_array = a.tostring()

for x in range(args.repeat):
  with StopWatch() as t:
    packed = blosc.pack_array(a)
    blosc.unpack_array(packed)
    del packed
  print("real: {0:.2f} cpu: {0:.2f}".format(t.time, t.cpu))
