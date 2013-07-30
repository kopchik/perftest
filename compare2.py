#!/usr/bin/env python3
from collections import OrderedDict
from os.path import basename
import argparse
import shlex
import sys
import os

from tests.benches import benches
from lib.utils import csv2dict
from useful.mystruct import Struct

import matplotlib as mpl
if 'DISPLAY' not in os.environ:
  mpl.use('Agg')
from matplotlib.colorbar import ColorbarBase
from matplotlib.ticker import MaxNLocator
from matplotlib import cm
from pylab import *


# from http://matplotlib.org/examples/pylab_examples/histogram_percent_demo.html
@FuncFormatter
def to_percent(y, position):
  # Ignore the passed in position. This has the effect of scaling the default
  # tick locations.
  s = str(100 * y)

  # The percent symbol needs escaping in latex
  if matplotlib.rcParams['text.usetex'] == True:
    return s + r'$\%$'
  else:
    return s + '%'




BARWIDTH = 0.7
styles = [
  dict(hatch="/", color="#25C600"),
  # dict(hatch="/", ls="dashed", color="#25C600", alpha=0.6),  # green
  dict(color="#2E9AFE"),  # blue
  dict(ls="dotted", color="#F78181"),  # red
  dict(color="#E6E6E6"),  # grey
  dict(hatch="\\", color="#2E9AFE"),
  dict(hatch="x", color="#40FF00"),
  dict(hatch='\\|/', color="#FACC2E"),
  dict(hatch="|+", color="white"),
  dict(hatch="/", color="#FA8258"), # chart orange
]
hatches = r"- +  x \\ * o O | .".split()
from itertools import cycle
styles = [style for style, _ in zip(cycle(styles), range(10))]

def enum_(it, offset=0):
  return [i+offset for i,_ in enumerate(it)]

profiles=dict(fx=Struct(), u2=Struct())
######
# U2 #
######
## brutality:
# cd ./results/u2/single/
# ../../../compare2.py sdagp matrix nginx pgbench wordpress blosc sdag ffmpeg integer
## sensitivity:
# ../../../compare2.py sdagp pgbench matrix sdag nginx wordpress ffmpeg blosc integer
exclude = """
L1-dcache-load-misses
L1-dcache-store-misses
L1-icache-load-misses
alignment-faults
branch-instructions
branch-load-misses
branch-misses
cache-misses
context-switches
cpu-clock
cpu-migrations
dTLB-load-misses
dTLB-store-misses
emulation-faults
iTLB-load-misses
major-faults
minor-faults
page-faults
ref-cycles
task-clock
stalled-cycles-frontend
L1-dcache-stores
"""
profiles['u2'].exclude = exclude

###########
# FX-8120 #
###########
# cd ./results/fx/cc_auto/notp/single/
## brutality
# ../../../../../compare2.py matrix nginx blosc pgbench wordpress sdag sdagp ffmpeg integer
## sensitivity
# ../../../../../compare2.py pgbench sdagp matrix blosc nginx sdag wordpress ffmpeg integer
exclude="""
L1-dcache-load-misses
L1-dcache-prefetch-misses
L1-dcache-prefetches
L1-dcache-stores
L1-icache-load-misses
L1-icache-prefetches
LLC-load-misses
LLC-loads
LLC-stores
alignment-faults
branch-load-misses
branch-misses
cache-misses
context-switches
cpu-clock
cpu-migrations
dTLB-load-misses
emulation-faults
iTLB-load-misses
major-faults
minor-faults
page-faults
task-clock
"""
profiles['fx'].exclude = exclude



def gen_plot(files, annotations=[], thr=0.3, _show=False, output=None):
  num = len(files)
  assert num > 0, "please provide at least one path"

  if not annotations:
    annotations = [basename(f) for f in files]

  data = [csv2dict(f) for f in files]
  bars = [[] for _ in data]
  labels = []
  key_order = sorted(data[0])


  key_order.remove('cycles')
  for k in key_order:
    values = []
    for datum, bar in zip(data, bars):
      values += [ datum[k] / datum['cycles'] ]
    if list(filter(lambda x: x>thr, values)):
      labels += [k]
      for bar, v in zip(bars, values):
        bar += [v]
    else:
      print("excluding", k)
  for b in bars:
    print(b, labels)

  ind = arange(len(labels))

  ## title
  # title(" | ".join(map(basename, fnames)))

  ## bars
  for i, bar in enumerate(bars):
    print(annotations[i])
    barh(ind-BARWIDTH/num*i, bar, height=BARWIDTH/num, label=annotations[i], **styles[i]) #color=cm.gist_ncar(1-1/num*i), hatch=hatches[i], alpha=0.7)

  ## reverse legend
  # handles, labels = gca().get_legend_handles_labels()
  # legend(handles[::-1], labels[::-1], loc='best')
  legend(loc="best")

  ## grid
  grid(lw=1)

  ## xaxis
  xaxis = gca().xaxis
  # xaxis.set_major_formatter(to_percent)
  # xaxis.set_major_locator(MaxNLocator(nbins=4, prune='upper'))
  xlabel("Avg. number of events per CPU cycle")
  xlim(0,1)

  ## set aspect
  # g = gca()
  # g.set_aspect(0.6)

  ## yaxis
  yticks(enum_(labels), labels)
  ylim(-0.5, len(labels)-0.5)

  tight_layout(pad=0.5)
  if output:
    savefig(output)
  if _show:
    show()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Analyze data from perf stat.')
  # parser.add_argument('-p', '--prefix', required=True, help="prefix path to data")
  # parser.add_argument('-b', '--bg', required=True, help="background task")
  # parser.add_argument('-f', '--fg', required=True, help="foreground task")
  parser.add_argument('-o', '--output', default=None, help="where to save image")
  # parser.add_argument('-s', '--sibling', action='store_const', default=False, const=True, help="sibling cores?")
  # parser.add_argument('-n', '--no-filter', action='store_const', default=True, const=True, help="Do not filter events")
  parser.add_argument('-t', '--threshold', type=float, default=0.05, help="foreground task")
  parser.add_argument('--show', action='store_const', const=True, default=False, help="show plot?")
  parser.add_argument('-f', '--files', nargs='+')
  parser.add_argument('-a', '--annotations', default=None, nargs='+')
  args = parser.parse_args()
  print(args)
  gen_plot(files=args.files, annotations=args.annotations, thr=args.threshold, _show=args.show, output=args.output)