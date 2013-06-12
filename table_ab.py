#!/usr/bin/env python3
from utils import csv2dict
import os
PATH="./results/fx/cc_auto/"

single = {}
for name in os.listdir(PATH+'/single/'):
  p = csv2dict(PATH+'/single/'+name)
  inps = p['instructions'] / p['cycles']
  single[name] = inps

double = {}
print(" &".join(sorted(single)), "\\\\")
for bg in sorted(single):
  print("{:12}".format(bg), end='')
  for fg in sorted(single):
    p = csv2dict(PATH+'/double/'+bg+'/'+fg)
    inps = p['instructions'] / p['cycles']
    ratio = inps/single[fg]
    double[bg,fg] = ratio
    print("& {:4.1f}".format((1-ratio)*100), end=' ')
  print(' \\\\')

print(double['integer','blosc'])
