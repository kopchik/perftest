#!/usr/bin/env python3
from lib.utils import csv2dict
import sys
import os

path_single = sys.argv[1]
path_double = sys.argv[2]

single = {}
for name in os.listdir(path_single):
  p = csv2dict(path_single+name)
  inps = p['instructions'] / p['cycles']
  single[name] = inps

summary = 0
double = {}
print("~           &", " &".join(sorted(single)), "\\\\")
for bg in sorted(single):
  print("{:12}".format(bg), end='')
  for fg in sorted(single):
    p = csv2dict(path_double+bg+'/'+fg)
    inps = p['instructions'] / p['cycles']
    ratio = inps/single[fg]
    double[bg,fg] = ratio
    percents = (1 - ratio) * 100
    if percents < 0:
        print("& \\green {:4.1f}".format(percents), end=' ')
    elif percents > 15:
        print("& \\red {:4.1f}".format(percents), end=' ')
    elif percents > 10:
        print("& \\orange {:4.1f}".format(percents), end=' ')
    else:
        print("& {:4.1f}".format(percents), end=' ')
    summary += percents
  print(' \\\\ \\hline')
print("Total percents of overhead:", summary)
print("average:", summary/len(single)**2)
