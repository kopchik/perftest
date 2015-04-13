#!/usr/bin/env python3

from useful.csv import Reader as CSVReader
from useful.small import invoke, dictzip
from useful.mstring import s


from argparse import ArgumentParser
from collections import OrderedDict
from statistics import mean,pstdev
from random import choice, random
from itertools import cycle
import numpy as np
import pickle
import os

import matplotlib as mpl
if 'DISPLAY' not in os.environ:
  mpl.use('Agg')
import pylab as p


def ci_student(a, confidence=0.9):
  from scipy.stats import sem, t
  import numpy as np

  n = len(a)
  mean = np.mean(a)  # mean value
  se = sem(a)        # standart error
  h = se * t.ppf((1+confidence)/2, n-1)
  # std  = np.std(y)
  # avgerr = np.mean([abs(mean-datum) for datum in y])
  # print("mean: {:.3f}, STD: {:.3f}, RSTD: {:.3%}, AVGERR: {:.3%} {:.3f}".format(mean, std, std/mean, avgerr/mean, se))
  return (2*h)/mean


def precision(samples, truevalue):
  return 1 - abs(1-mean(samples)/truevalue)

def precision2(samples1, samples2):
  return 1 - abs(1-mean(samples1)/mean(samples2))


def single(path, label=None, lw=4, ms=10, **kwargs):
  lw = float(lw)
  with open(path) as csvfile:
    ts, cycles = [], []
    cur_cycles = 0
    cur_instr = 0
    for t, val, cnt in CSVReader(csvfile, type=(float,int,str)):
      if cnt == 'instructions':
        cur_instr = val
      elif cnt == 'cycles':
        cur_cycles = val
        cycles.append(cur_instr/cur_cycles)
        ts.append(t)
      else:
        raise Exception("I accept only cycles and instructions")
  print(ts[:10], cycles[:10])
  #args = {}
  #if color: args['color'] = color
  p.plot(ts, cycles, label=label, lw=lw, ms=ms, **kwargs)


def annotate(y:float, start:float, stop:float, text, notch:float=0.07, color='black', lw:float=2):
  # from http://stackoverflow.com/questions/7684475/plotting-labeled-intervals-in-matplotlib-gnuplot
  p.hlines(y, start, stop, color, lw=lw*2)
  p.vlines(start, y+notch, y-notch, color, lw=lw)
  p.vlines(stop, y+notch, y-notch, color, lw=lw)
  p.text((stop-start)/2, y+0.015 , text, horizontalalignment='center', fontsize=30)


def myboxplot(data, *args, labels=None, legend=["isolated env", "frozen env"], **kwargs):
  alpha=0.6
  positions = [n+y+1 for n,y in zip(range(len(data)),cycle([+0.2,-0.2]))]
  box = p.boxplot(data, *args, positions=positions, patch_artist=True, **kwargs)
  p.plot(positions, [mean(d) for d in data], 'r*', markeredgecolor='red', lw=10)
  if labels:
    p.xticks(np.arange(len(labels))*2+1.5, labels, rotation=25)

  # set colors
  for patch, color in zip(box['boxes'], cycle(['green', 'blue'])):
    patch.set_facecolor(color)
    patch.set_alpha(alpha)

  iso = p.Rectangle((0, 0), 1, 1, fc='green', ec='black', alpha=alpha)
  fro = p.Rectangle((0, 0), 1, 1, color='blue', ec='black', alpha=alpha)
  p.legend([iso, fro], legend)


  return box

def analyze_reverse2(data):
  data = pickle.load(open(data, 'rb')).result
  isolated = data.isolated
  shared = data.shared
  plots, labels = [], []
  tuples = []
  for test, isolated, shared in dictzip(isolated, shared):
     prec = precision2(shared, isolated)
     tuples.append((test, isolated, shared, prec))
  tuples = sorted(tuples, key=lambda x: x[3])
  for test, isolated, shared, prec in tuples:
      # if prec >0.1: continue
      plots.append(isolated)
      plots.append(shared)
      labels.append("{} {:.1%}".format(test, prec))
  myboxplot(plots, labels=labels)


def subsampling(data):
  data = pickle.load(open(data, 'rb')).result
  isolated = data.standard
  shared = data.withskip
  plots, labels = [], []
  tuples = []
  for test, isolated, shared in dictzip(isolated, shared):
     prec = precision2(shared, isolated)
     tuples.append((test, isolated, shared, prec))
  tuples = sorted(tuples, key=lambda x: x[0])
  for test, isolated, shared, prec in tuples:
      # if prec >0.1: continue
      plots.append(isolated)
      plots.append(shared)
      labels.append("{} {:.1%}".format(test, prec))
  myboxplot(plots, labels=labels)


def analyze_reverse(ref, exp, prec:float=0.95, maxtries:int=50, mode='hist', confidence:float=0.9):
  refdata = pickle.load(open(ref, 'rb')).result
  expdata = pickle.load(open(exp, 'rb')).result
  # unpack reference data
  for k,v in refdata.items():
    refdata[k] = v[0]

  # HIST
  if mode == 'hist':
    for i, (test, truevalue) in enumerate(refdata.items(), 1):
      measurements = expdata[test]
      label = " -> ".join(test)
      p.subplot(12,1,i)
      p.xlim(0,2)
      p.hist(measurements, bins=50, label=label, normed=True, histtype='stepfilled', linewidth=2, alpha=0.7)
    p.subplots_adjust(left=0, right=1, top=1, bottom=0)
  # MONTE CARLO
  elif mode == 'montecarlo':
    results = []
    failures = 0
    for test, truevalue in refdata.items():
      for _ in range(1000):
        samples = []
        for x in range(maxtries):
          samples.append(choice(expdata[test]))
          # samples.append(random())  # absolute random junk
          if precision(samples, truevalue) > prec:
            num = len(samples)
            if num > 50: print("achtung!")
            results.append(num)
            # print(truevalue, samples)
            break
        else:
          # we failed to achieve precision
          failures += 1
    frate = failures/(len(results)+failures)
    print("-= for precision %s =-" % prec)
    print("mean={:.2f}({:.0%}), failure rate={:.2%}".format(mean(results), pstdev(results), frate))
  # CONFIDENCE INTERVAL
  elif mode == 'ci':
    for test, truevalue in sorted(refdata.items()):
      ci = ci_student(expdata[test], confidence=0.95)
      print("{}: ci {:.2%}".format(test, ci))
  else:
    sys.exit(s("unknown mode ${mode}"))


def compare(data1, data2, legend):
  assert data1, "data1 cannot be empty"
  assert data2, "data2 cannot be empty"
  def ipc(data): return [t[0]/t[1] for t in data]

  data, labels = [], []
  for test, p, s in sorted(dictzip(data1,data2)):
    print(test, p[:2], s[:2])
    labels.append(test)
    data.append(p)
    data.append(ipc(s))
    myboxplot(data, labels=labels, legend=legend, notch=True)

def cmp(path1, path2):
  pure   = pickle.load(open(path1, 'rb')).result.pure
  shared = pickle.load(open(path2, 'rb')).result
  return compare(pure, shared, legend=["isolated meas.", "shared meas."])

def delay(path):
  struct = pickle.load(open(path, 'rb'))
  without   = struct.result.without
  withdelay = struct.result.withdelay
  return compare(without, withdelay, legend=["without delay", "with delay"])

def distribution(data, mode='hist'):
  data = pickle.load(open(data, 'rb'))
  pure = data.result.pure   # data from pure performance isolation
  quasi = data.result.quasi # data from quasi isolation
  if mode == 'hist':
    for i, (test, ref, measurements) in enumerate(dictzip(pure, quasi)):
      # print(test, len(ref), len(measurements))
      print(ref)
      p.subplot(4,2,i+1)
      p.title(test)
      p.hist(ref, bins=50, label="real isolation", alpha=0.7)
      p.hist(measurements, bins=50, label="quasi-isolation", alpha=0.7)
      p.legend(loc="best")
      p.xlim(0,3)

  elif mode == 'boxplot':
    labels = []
    data = []
    for i, (test, ref, measurements) in enumerate(sorted(dictzip(pure, quasi))):
      labels.append(test)
      data.append(ref)
      data.append(measurements)
    box = myboxplot(data, labels=labels, notch=True)


def analyze(real, samples, skip=0, thr=0.9):
  real = pickle.load(open(real, 'rb'))
  samples = pickle.load(open(samples, 'rb'))
  thr=float(thr)

  def flatten(measurements):
    shared, exclusive = [], []
    for es, ss in measurements:
      exclusive.extend(es[skip:])
      shared.extend(ss[skip:])
    return exclusive, shared

  true_values = OrderedDict()
  for vm, measurements in real.results.items():
    shared, exclusive = flatten(measurements)
    true_values[vm] = mean(shared)/mean(exclusive)
  print(true_values)

  means = OrderedDict()
  nums = []
  avgms, avgdevs = [], []
  #for vm, measurements in sorted(samples.results.items()):
  for vm, measurements in sorted(samples.results.items()):
    print("calculating", vm)
    shared, exclusive = flatten(measurements)
    def myfilter(l): return [e for e in l if e != 0]
    shared = myfilter(shared)
    exclusive = myfilter(exclusive)
    ns = []
    true = true_values[vm]
    for _ in range(1000):
      sh_samples, exc_samples = [], []
      n = 0
      while True:
        n += 1
        sh_samples.append(choice(shared))
        exc_samples.append(choice(exclusive))
        cur = mean(sh_samples)/mean(exc_samples)
        prec = 1 - abs(1-cur/true)
        if prec > thr:
          ns.append(n)
          break
        if n > 20:
          print(vm, "max precision:", prec)
          break
    if not ns:
      print("no data points for", vm)
      continue
    nums.append(ns)
    #m = mean(ns)
    #d = pstdev(ns)
    #rd = d/m*100
    #avgdevs.append(rd)
    #avgms.append(m)
    #print("{vm}: {m:.1f} {rd:.1f}%".format(vm=vm, m=m,d=d,rd=rd))
    #means[vm]=mean(nums)
  ticks = real.mapping
  p.xticks(range(len(ticks)), ticks)
  p.boxplot(nums)
  #import pdb; pdb.set_trace()
  #print(mean(avgms), mean(avgdevs))
  #print("RESULT for thr=%s:" % thr, result)


def ragged(path, label=None, lw=4, color=None):
  lw = float(lw)
  with open(path) as csvfile:
    ts, cycles = [], []
    for t, c, _, typ in CSVReader(csvfile, type=(float,int,str,str)):
        cycles.append(c)
        ts.append(t)
        assert typ == 'cycles'
  print(ts[:10], cycles[:10])
  args = {}
  if color: args['color'] = color
  p.plot(ts, cycles, label=label, lw=lw, **args)

if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-o', '--output', default=None, help="where to save image")
  parser.add_argument('--show', action='store_const', const=True, default=False, help="show plot?")
  parser.add_argument('-t', '--title', help="plot title")
  parser.add_argument('-a', '--annotations', default=None, nargs='+')
  parser.add_argument('-x', '--xlabel', default=None)
  parser.add_argument('--xlim', type=float, nargs=2, help="limit X axis of the plot")
  parser.add_argument('--ylim', type=float, nargs=2, help="limit Y axis of the plot")
  parser.add_argument('-y', '--ylabel', default=None)
  parser.add_argument('-f', '--freq', type=int, default=None, help="CPU frequency")
  parser.add_argument('-p', '--plots', nargs='+', required=True)
  args = parser.parse_args()
  print(args)

  for plot in args.plots:
    func, params = invoke(plot, globals())
    print(params)
    func(**params)

  if args.output or args.show:
    p.legend(loc="best")
    p.tight_layout(pad=0.5)
    font = {'family' : 'normal',
            'weight' : 'bold',
            'size'   : 18}
    p.rc('font', **font)
    if args.xlabel: p.xlabel(args.xlabel)
    if args.ylabel: p.ylabel(args.ylabel)
    if args.xlim: p.xlim(args.xlim)
    if args.ylim: p.ylim(args.ylim)
    if args.title: p.title(args.title)
    if args.output:
      p.savefig(args.output, dpi=300, bbox_inches='tight')
    # p.tight_layout()
    if args.show: p.show()
