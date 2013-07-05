#!/usr/bin/env python3
from utils import csv2dict
import sys
import os

path_single = sys.argv[1]
path_double = sys.argv[2]

single = {}
for name in os.listdir(path_single):
  p = csv2dict(path_single+name)
  inps = p['instructions'] / p['cycles']
  single[name] = inps

double = {}
print(" &".join(sorted(single)), "\\\\")
for bg in sorted(single):
  print("{:12}".format(bg), end='')
  for fg in sorted(single):
    p = csv2dict(path_double+bg+'/'+fg)
    inps = p['instructions'] / p['cycles']
    ratio = inps/single[fg]
    double[bg,fg] = ratio
    print("& {:4.1f}".format((1-ratio)*100), end=' ')
  print(' \\\\')

print(double['integer','blosc'])
