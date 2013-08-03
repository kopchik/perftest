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


def perfbars(files, annotations=[], thr=0.01, _show=False, output=None, _title=None):
  figure()
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

  if _title:
    title(_title, weight="semibold")
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
  # xlim(0,1)

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



def stability(paths, show=False, output=None):
  # COLOR = "#548BE3"
  COLOR = "#8CB8FF"
  pltnum = len(paths)//2 + len(paths)%2
  for i, fname in enumerate(paths):
    with open(fname) as fd:
      values = []
      t = fd.readline().strip("#")
      for l in fd.readlines():
        values += [float(l.strip())]
      p.subplot(pltnum, 2, i+1)
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
    p.savefig(output)
  if show:
    p.show()