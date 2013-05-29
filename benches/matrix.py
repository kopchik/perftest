#!/usr/bin/env python3
from useful.bench import StopWatch

import numpy as np
import gc; gc.disable()
import argparse
import sys

parser = argparse.ArgumentParser(description='Run experiments')
parser.add_argument('-d', '--debug', type=float, default=10, help="measurement time")
parser.add_argument('-s', '--size', type=int, default=256, help="matrix size (N means NxN size)")
parser.add_argument('-r', '--repeat', '--repeats', type=int, default=10, help="number of test repeats")
args = parser.parse_args()


A=np.random.randn(args.size, args.size)
B=np.random.randn(args.size, args.size)
#avg = Avg(report=repeats)
#print("for matrix {0}x{0} ....".format(size))
for y in range(args.repeat):
    with StopWatch() as t:
      np.dot(A, B)
    print("{n} Matrices {0}x{0}: real: {1:.2f} cpu: {2:.2f}".format(args.size, t.time, t.cpu, n=y))
    #avg.append(result)
