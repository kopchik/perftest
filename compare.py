#!/usr/bin/env python3
from utils import csv2dict
from pylab import *
import sys

def die(reason): sys.exit(reason)
def myrange(start, interval, repeats):
  for x in range(repeats):
    yield start
    start += interval

def main(argv):
  data = []
  figpath = argv[1]
  files = argv[2:]
  if not files:
    die("please specify datasets to compare")
  for f in files:
    data += [csv2dict(f)]
  reference = data.pop(0)

  # calculations
  ticks = []
  values = []
  ratio = []
  for k,vref in reference.items():
    if k not in data[0]:
      print("not in second dataset:", k)
      continue
    v = data[0][k]
    if v == 0 or vref == 0: continue
    r = v/vref-1
    if abs(r) <0.2: continue  # skip parameters that didn't change much
    if k == 'cpu-migrations': continue  # skip irrelevant counters
    ratio += [r]
    ticks += [k]
    values += [v]

  # plotting
  barh(list(myrange(-0.4, 1, len(ratio))), ratio)
  yticks(range(len(ticks)), ticks, rotation=0)
  axvline(linewidth=4, color='g')
  xlim([-1.2,5])
  subplots_adjust(left=0.34)
  xticks(arange(-1,5), ('-100%','0', '100%', '200%', '300%', '400%'))
  for i, v in enumerate(values):
    color = 'red'
    r = ratio[i]
    v = values[i]
    x = r + 0.07 if r > 0 else r - 0.2
    if x > 4: x = 4; color = 'white'
    label = "{}".format(int(v))
    text(x, i-0.16, label, fontsize=18, color=color)

  # bar(list(myrange(-0.4, 1, len(ratio))), ratio)
  # xticks(range(len(ticks)), ticks, rotation=60)
  # axhline(linewidth=4, color='g')
  # subplots_adjust(bottom=0.2)
  #savefig("/home/exe/github/perf2013paper/pic/blosc_bars.eps")
  savefig(figpath)
  show()

if __name__ == '__main__':
  main(sys.argv)
