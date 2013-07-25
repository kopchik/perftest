#!/usr/bin/env python3
from tests.benches import benches
from lib.utils import csv2dict
import argparse
import shlex
import sys
import os

import matplotlib as mpl
if 'DISPLAY' not in os.environ:
  mpl.use('Agg')
from matplotlib.ticker import MaxNLocator
from pylab import *


BARWIDTH = 0.8
# BARCOLOR = "#78A4EB"
# BARCOLOR = "#6C9EF0"
BARCOLOR = "#548BE3"

def die(reason):
  sys.exit(reason)


def myrange(start, interval, repeats):
  for x in range(repeats):
    yield start
    start += interval


def enum_(it, offset=0):
  return [i+offset for i,_ in enumerate(it)]


def fmt_int(v):
  if   v> 10**9: r = "{:.1f}B".format(v/10**9)
  elif v> 10**6: r = "{:.1f}M".format(v/10**6)
  elif v> 1000:  r = "{:.1f}K".format(v/1000)
  else: r = "{:.1f}".format(v)
  return r


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


def main(argv):
  data = []
  files = []

  parser = argparse.ArgumentParser(description='Analyze data from perf stat.')
  parser.add_argument('-p', '--prefix', required=True, help="prefix path to data")
  parser.add_argument('-b', '--bg', required=True, help="background task")
  parser.add_argument('-f', '--fg', required=True, help="foreground task")
  parser.add_argument('-o', '--output', help="where to save image")
  parser.add_argument('-s', '--sibling', action='store_const', default=False, const=True, help="sibling cores?")
  parser.add_argument('-n', '--no-filter', action='store_const', default=False, const=True, help="Do not filter events")
  parser.add_argument('--show', action='store_const', const=True, default=False, help="show plot?")
  args = parser.parse_args(argv[1:])
  # print(args)

  files.append("{prefix}/single/{fg}".format(**vars(args)))
  if args.sibling:
    files.append("{prefix}/double_near/{bg}/{fg}".format(**vars(args)))
  else:
    path = "{prefix}/double_far/{bg}/{fg}".format(**vars(args))
    try:
      os.stat(path)
    except FileNotFoundError:
      path = "{prefix}/double/{bg}/{fg}".format(**vars(args))
    files.append(path)

  # convert csv to dict
  for f in files:
    data += [csv2dict(f)]
  reference = data.pop(0)

  # calculations
  mtime = data[0]['task-clock'] / 1000
  labels = []
  values = []
  ratio = []
  for k,vref in reference.items():
    if k not in data[0]:
      print("not in second dataset:", k)
      continue
    if k in ['cpu-clock', 'task-clock']:
      continue
    v = data[0][k]
    if v == 0 or vref == 0: continue
    r = v/vref-1
    if not args.no_filter:
      if abs(r) <0.05 and k != "stalled-cycles-backend":
        continue  # skip parameters that didn't change much
      if v/mtime < 1000:
        continue
    if k == 'cpu-migrations': continue  # skip irrelevant counters
    ratio += [r]
    labels += ["{name} [{freq}]".format(name=k, freq=fmt_int(v/mtime))]
    values += [v]

  # autoscale()
  ## enlarge font size
  tick_params(axis='both', which='major', labelsize=16)
  ## draw bars
  bars = barh(enum_(ratio, offset=-BARWIDTH/2), ratio, height=BARWIDTH, color=BARCOLOR)
  yticks(enum_(labels), labels)
  ## vertical line
  axvline(linewidth=4, color='g')
  ## adjust y to fit all plots
  ylim(-0.5, len(values)-0.5)
  ## display grid
  grid(lw=1)
  ## show X in percents
  xaxis = gca().xaxis
  xaxis.set_major_formatter(to_percent)
  xaxis.set_major_locator(MaxNLocator(nbins=5, prune='upper'))
  xmin, xmax = xlim()
  if xmin >= 0:
    xmin = -(xmax-xmin)/50
  xlim(xmin,xmax)
  ## adjust left margin to fit long counter names
  # subplots_adjust(left=0.34)
  tight_layout(pad=0.5)

  if args.output:
    savefig(args.output)
  if args.show:
    show()
  figure()  # start new figure

def regen(src, dst, sibling=False):
  for bg in benches:
    for fg in benches:
      try:
        os.makedirs("{dst}/{bg}".format(dst=dst, bg=bg))
      except FileExistsError:
        pass
      cmd = './compare.py -p {src} -f {fg} -b {bg} -o "{dst}/{bg}/{fg}.png"' \
            .format(**locals())
      cmd = shlex.split(cmd)
      if sibling: cmd += ["-s"]
      # print(cmd)
      main(cmd)

if __name__ == '__main__':
  if len(sys.argv) > 1:
    main(sys.argv)
  else:
    print("u2")
    regen("./results/u2/", "./static/u2/")
    print("fx far")
    regen("./results/fx/cc_auto/notp/", "./static/fx_far/")
    print("fx near")
    regen("./results/fx/cc_auto/notp/", "./static/fx_near/", sibling=True)
    print("panda")
    regen("./results/panda/notp/", "./static/panda/")
