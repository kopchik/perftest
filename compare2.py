#!/usr/bin/env python3
from collections import OrderedDict
from tests.benches import benches
from lib.utils import csv2dict
from useful.mystruct import Struct
import argparse
import shlex
import sys
import os

import matplotlib as mpl
if 'DISPLAY' not in os.environ:
  mpl.use('Agg')
from matplotlib.colorbar import ColorbarBase
from matplotlib.ticker import MaxNLocator
from os.path import basename
from pylab import *

BARWIDTH = 0.8
styles = [
  dict(color="#548BE3"),  # blue
  dict(color="#25C600", alpha=0.5),  # green
  dict(color="#CB0037", alpha=0.5),  # red
]


def enum_(it, offset=0):
  return [i+offset for i,_ in enumerate(it)]


fnames = sys.argv[1:]
num = len(fnames)
assert num > 0, "please provide at least one path"

csvs = []
for fname in fnames:
  csvs += [csv2dict(fname)]

charts = [[] for _ in csvs]
key_order = sorted(csvs[0])
key_order.remove('cycles')
key_order.remove('ref-cycles')
key_order.remove('task-clock')
key_order.remove('cpu-clock')
key_order.remove('cpu-migrations')
key_order.remove('emulation-faults')
key_order.remove('major-faults')
key_order.remove('minor-faults')
key_order.remove('page-faults')
key_order.remove('alignment-faults')
key_order.remove('context-switches')
# key_order = ['cycles']
ind = arange(len(key_order))
for csv, chart in zip(csvs, charts):
  for k in key_order:
    v = csv[k] / csv['cycles']
    chart += [v]


title(" | ".join(map(basename, fnames)))
for i, chart in enumerate(charts):
  barh(ind+BARWIDTH/num*i-BARWIDTH/2, chart, height=BARWIDTH/num, log=True, **styles[i])
# barh(enum_(ratios, offset=-BARWIDTH/2), ratios, height=BARWIDTH, color=BARCOLOR)
# barh(enum_(ratios, offset=-BARWIDTH/3), ratios, height=BARWIDTH*0.3, color="red")
yticks(enum_(key_order), key_order)
ylim(-0.5, len(key_order)-0.5)
tight_layout(pad=0.5)
show()