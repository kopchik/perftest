#!/usr/bin/env python3

from os.path import basename
from itertools import cycle
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
import pylab as p
from scipy.stats import norm

BARWIDTH = 0.8


# from http://matplotlib.org/examples/pylab_examples/histogram_percent_demo.html
@p.FuncFormatter
def to_percent(y, position):
  # Ignore the passed in position. This has the effect of scaling the default
  # tick locations.
  s = str(100 * y)

  # The percent symbol needs escaping in latex
  if mpl.rcParams['text.usetex'] == True:
    return s + r'$\%$'
  else:
    return s + '%'

def average(a):
  return sum(a)/len(a)


# styles = [
#   dict(hatch="/", color="#25C600"),
#   # dict(hatch="/", ls="dashed", color="#25C600", alpha=0.6),  # green
#   dict(color="#2E9AFE"),  # blue
#   dict(ls="dotted", color="#F78181"),  # red
#   dict(color="#E6E6E6"),  # grey
#   dict(hatch="\\", color="#2E9AFE"),
#   dict(hatch="x", color="#40FF00"),
#   dict(hatch='\\|/', color="#FACC2E"),
#   dict(hatch="|+", color="white"),
#   dict(hatch="/", color="#FA8258"), # chart orange
# ]
styles = [
  dict(color="#424242"),
  dict(color="#6E6E6E"),
  dict(color="#BDBDBD"),
  dict(color="#E6E6E6"),
  dict(color="#FAFAFA"),
  # dict(color=""),
]

styles = [style for style, _ in zip(cycle(styles), range(10))]

def enum_(it, offset=0):
  return [i+offset for i,_ in enumerate(it)]


######
# U2 #
######

## brutality:
# cd ./results/u2/single/
# ../../../compare2.py sdagp matrix nginx pgbench wordpress blosc sdag ffmpeg integer
## sensitivity:
# ../../../compare2.py sdagp pgbench matrix sdag nginx wordpress ffmpeg blosc integer

###########
# FX-8120 #
###########
# cd ./results/fx/cc_auto/notp/single/
## brutality
# ../../../../../compare2.py matrix nginx blosc pgbench wordpress sdag sdagp ffmpeg integer
## sensitivity
# ../../../../../compare2.py pgbench sdagp matrix blosc nginx sdag wordpress ffmpeg integer


def perfbars(files, annotations=[], thr=0.01, show=False, output=None, title=None, quiet=False, key_order=None):
  p.figure()
  num = len(files)
  assert num > 0, "please provide at least one path"

  if not annotations:
    annotations = [basename(f) for f in files]

  data = [csv2dict(f) for f in files]
  bars = [[] for _ in data]
  labels = []

  if key_order:
    print("WITH KEY_ORDER THRESHOLD IS ALWAYS 0")
    thr = 0.0
  if not key_order:
    key_order = sorted(data[0])
  if 'cycles' in key_order:
    key_order.remove('cycles')

  for k in reversed(key_order):
    values = []
    for datum, bar in zip(data, bars):
      values += [ datum[k] / datum['cycles'] ]
    if list(filter(lambda x: x>thr, values)):
      labels += [k]
      for bar, v in zip(bars, values):
        bar += [v]
    else:
      if not quiet: print("excluding", k)
  for b in bars:
    if not quiet: print(b, labels)

  ind = p.arange(len(labels))
  print("ind", ind)

  if title:
    title=title.replace(r"\n", "\n")
    p.title(title, weight="semibold")
  ## title
  # title(" | ".join(map(basename, fnames)))

  ## bars
  for i, bar in enumerate(bars):
    p.barh(ind+BARWIDTH*(num-2*i-2)/(2*num), bar, height=BARWIDTH/num, label=annotations[i],
    #**styles[i]) #
    color=cm.Greys_r((i+0.4)/len(bars)*0.8))
    #color=cm.gist_ncar(1-1/num*i), hatch=hatches[i], alpha=0.7)

  ## reverse legend
  # handles, labels = gca().get_legend_handles_labels()
  # legend(handles[::-1], labels[::-1], loc='best')
  p.legend(loc="best")

  ## grid
  p.grid(lw=1)

  ## xaxis
  xaxis = p.gca().xaxis
  # xaxis.set_major_formatter(to_percent)
  # xaxis.set_major_locator(MaxNLocator(nbins=4, prune='upper'))
  p.xlabel("Avg. number of events per CPU cycle")
  # xlim(0,1)

  ## set aspect
  # g = gca()
  # g.set_aspect(0.6)

  ## yaxis
  p.yticks(enum_(labels), labels)
  p.ylim(-0.5, len(labels)-0.5)

  p.tight_layout(pad=0.5)
  if output:
    p.savefig(output)
  if show:
    p.show()



def stability(paths, show=False, output=None, annotations=None, aspect=2):
  # COLOR = "#548BE3"
  COLOR = "#8CB8FF"
  figure = p.figure()
  pltnum = len(paths)//2 + len(paths)%2
  for i, fname in enumerate(paths):
    with open(fname) as fd:
      values = []
      t = fd.readline().strip("#")
      for l in fd.readlines():
        values += [float(l.strip())]
      p.subplot(pltnum, 2, i+1)

      ## title
      if annotations:
        p.title(annotations[i])
      else:
        p.title(t)
      avg = average(values)
      percents = list(map(lambda x: avg/x-1, values))
      n, bins, patches = p.hist(percents,
        bins=50, normed=True,
        histtype='bar', color=COLOR)

      mu, sigma = norm.fit(percents)
      y = p.normpdf(bins, mu, sigma)
      p.plot(bins, y, 'r-', linewidth=3)
      p.xlim(min(bins), max(bins))

      ## set aspect
      xmin, xmax = p.xlim()
      ymin, ymax = p.ylim()
      xr = xmax - xmin
      yr = ymax - ymin
      aspect = xr/yr/2
      g = p.gca()
      g.set_aspect(aspect)
      # p.figaspect(aspect)


    ## remove y axis
    yaxis = p.gca().yaxis
    yaxis.set_major_locator(MaxNLocator(nbins=4, prune='lower'))
    # yaxis.set_visible(False)

    ## xaxis
    xaxis = p.gca().xaxis
    xaxis.set_major_formatter(to_percent)
    xaxis.set_major_locator(MaxNLocator(nbins=5, prune='lower'))

  p.tight_layout(pad=0.5)
  if output:
    p.savefig(output, bbox_inches='tight')
  if show:
    p.show()
