#!/usr/bin/env python3
from lib.utils import csv2dict
from collections import defaultdict, OrderedDict
from scipy.stats.stats import pearsonr, linregress
from operator import itemgetter
from itertools import product
import pylab as p
import sys
import os


brutality = defaultdict(int)
sensitivity = defaultdict(int)

path_single = sys.argv[1] + '/'
path_double = sys.argv[2] + '/'

def gettotal(hpc1, hpc2, params):
  total = 0
  for p in params:
    total += hpc1[p] + hpc2[p]
  return total

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
  hpc = csv2dict(path_single+name)
  inps = hpc['instructions'] / hpc['cycles']
  single[name] = inps

summary = 0
double = {}
print("~           &", " &".join(sorted(single)), "\\\\")
for bg in sorted(single):
  print("{:12}".format(bg), end='')
  for fg in sorted(single):
    hpc = csv2dict(path_double+bg+'/'+fg)
    inps = hpc['instructions'] / hpc['cycles']
    ratio = inps/single[fg]
    double[bg,fg] = ratio
    percents = (1 - ratio)* 100
    # if percents < 0:
    #     print("& \\green {:4.1f}".format(percents), end=' ')
    # elif percents > 15:
    #     print("& \\red {:4.1f}".format(percents), end=' ')
    # elif percents > 10:
    #     print("& \\orange {:4.1f}".format(percents), end=' ')
    # else:
    print("{:4.1f},".format(percents), end=' ')
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

print("\n================\n")

def norm(d):
  cycles = d['cycles']
  for k,v in d.items():
    d[k] = v/cycles
  return d

class hpcs:
  single = {}
  double = {}

for name in os.listdir(path_single):
  hpc = csv2dict(path_single+name)
  hpc = norm(hpc)
  hpcs.single[name] = norm(hpc)

for bg in sorted(single):
  for fg in sorted(single):
    hpc = csv2dict(path_double+bg+'/'+fg)
    hpc = norm(hpc)
    hpcs.double[bg,fg] = hpc



correlation = {}
pvalue = {}
for counter in hpcs.single['sdag']:
  bruts = []
  stats = []
  for (bname, brut) in sorted_dict(sensitivity):
    bruts += [brut]
    stats += [hpcs.single[bname][counter]]
  cor, pv = pearsonr(bruts, stats)

  if pv < 0.05:
    correlation[counter] = cor
    pvalue[counter] = pv
for cnt, cor in sorted_dict(correlation):
  print("{cnt:22} & {cor: 2.3f} & {pval:2.1%} \\\ \hline".format(cnt=cnt, cor=cor, pval=pvalue[cnt]))


counters = defaultdict(list)

plotdata = {}
degradations = []
for t2, t1 in product(sorted(hpcs.single), repeat=2):
  # print(t1, t2)
  s1 = hpcs.single[t1]
  s2 = hpcs.single[t2]
  d1 = hpcs.double[t1,t2]
  d2 = hpcs.double[t2,t1]

  naive   = s1['instructions'] + s2['instructions']
  actual  = d1['instructions'] + d2['instructions']
  degr = actual / naive
  degradations += [degr]

  for k, v1 in s1.items():
    v2 = s2[k]
    total = v1 + v2
    counters[k] += [total]


  # total = gettotal(shpc1, shpc2, ['LLC-stores', 'LLC-loads'])
  total = gettotal(s1, s2, ['instructions'])
  plotdata[total] = degr

for counter,v in counters.items():
  cor, pv = pearsonr(v, degradations)
  if pv < 0.1:
    print ("{:25} {: .3f} {:2.1%}".format(counter, cor, pv*100))


if plotdata:
  X = sorted(list(plotdata.keys()))
  Y = [plotdata[x] for x in X]
  print(linregress(X,Y))
  p.xlabel("counters")
  p.ylabel("degradatation")
  p.plot(X, Y, '-o')
  p.show()