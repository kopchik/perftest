#!/usr/bin/env python3
from lib.utils import csv2dict
from collections import defaultdict, OrderedDict
from operator import itemgetter
import sys
import os

path_single = sys.argv[1]
path_double = sys.argv[2]

def sorted_dict(d):
  return sorted(d.items(), key=itemgetter(1), reverse=True)

def fmt(v):
  return "{:.1f}".format(v)

def print_tbl(data, header=None):
  if header:
    print(header)
  for k, v in sorted_dict(data):
    # v = brutality[k]
    line = "{k:<10} & {v:.1f}\% \\\ \hline".format(k=k, v=v)
    print(line)
  print()

def print_double(data1, data2):
  sorted_data1 = sorted_dict(data1)
  sorted_data2 = sorted_dict(data2)
  iterator = zip(sorted_data1, sorted_data2)
  for (k1,v1), (k2,v2) in iterator:
    line = r"{k1:<10} & {v1:>5.1f}\% & {k2:<10} & {v2:>5.1f}\% \\ \hline".format(**locals())
    print(line)

single = {}
for name in os.listdir(path_single):
  p = csv2dict(path_single+name)
  inps = p['instructions'] / p['cycles']
  single[name] = inps

brutality = defaultdict(int)
sensitivity = defaultdict(int)
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
    percents = (1 - ratio)* 100
    if percents < 0:
        print("& \\green {:4.1f}".format(percents), end=' ')
    elif percents > 15:
        print("& \\red {:4.1f}".format(percents), end=' ')
    elif percents > 10:
        print("& \\orange {:4.1f}".format(percents), end=' ')
    else:
        print("& {:4.1f}".format(percents), end=' ')
    summary += percents
    brutality[bg] += percents
    sensitivity[fg] += percents
  print(' \\\\ \\hline')
print("Total percents of overhead:", summary)
print("average:", summary/len(single)**2)

# normalize
for k,v in brutality.items():
  brutality[k] /= len(single)
for k,v in sensitivity.items():
  sensitivity[k] /= len(single)

# print_tbl(brutality, header="Brutality")
# print_tbl(sensitivity, header="Sensitivity")
print_double(brutality, sensitivity)

# print("sensitivity")
# for k in key_order:
#   v = sensitivity[k]
#   print(k, fmt(v))
