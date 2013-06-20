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
  ticks = []
  files = argv[1:]
  if not files:
    die("please specify datasets to compare")
  for f in files:
    data += [csv2dict(f)]
  reference = data.pop(0)
  ratio = []
  for k,vref in reference.items():
    if k not in data[0]:
      print("not in second dataset:", k)
      continue
    v = data[0][k]
    if v == 0 and vref == 0: continue
    r = v/vref-1
    if abs(r) <0.3: continue 
    ratio += [r]
    ticks += [k]
  barh(list(myrange(-0.4, 1, len(ratio))), ratio)
  yticks(range(len(ticks)), ticks, rotation=0)
  axvline(linewidth=4, color='g')
  xlim([-1.2,5])
  subplots_adjust(left=0.34)
  xticks(arange(-1,5), ('-100%','0', '100%', '200%', '300%', '400%'))

  # bar(list(myrange(-0.4, 1, len(ratio))), ratio)
  # xticks(range(len(ticks)), ticks, rotation=60)
  # axhline(linewidth=4, color='g')
  # subplots_adjust(bottom=0.2)
  savefig("/home/exe/github/perf2013paper/pic/blosc_bars.eps")
  show()

if __name__ == '__main__':
  main(sys.argv)
