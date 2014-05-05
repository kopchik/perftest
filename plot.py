#!/usr/bin/env python3
from useful.csv import Reader as CSVReader
from argparse import ArgumentParser
import pylab as p

import matplotlib as mpl
import os
if 'DISPLAY' not in os.environ:
  mpl.use('Agg')



def parse(cmd):
  return dict(s.split('=') for s in cmd.split('|'))

def single(path, label=None, lw=4, color=None):
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
  args = {}
  if color: args['color'] = color
  p.plot(ts, cycles, label=label, lw=lw, **args)


def annotate(y, start, stop, text, notch=0.07, color='black', lw=2):
  # from http://stackoverflow.com/questions/7684475/plotting-labeled-intervals-in-matplotlib-gnuplot
  lw = float(lw)
  y = float(y)
  start = float(start)
  stop = float(stop)
  notch = float(notch)

  p.hlines(y, start, stop, color, lw=lw*2)
  p.vlines(start, y+notch, y-notch, color, lw=lw)
  p.vlines(stop, y+notch, y-notch, color, lw=lw)
  p.text((stop-start)/2, y+0.015 , text, horizontalalignment='center', fontsize=30)


import pickle
from statistics import mean,pstdev
from collections import OrderedDict
from random import choice

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

  result = OrderedDict()
  for vm, measurements in sorted(samples.results.items()):
    shared, exclusive = flatten(measurements)
    nums = []
    true = true_values[vm]
    for _ in range(10000):
      sh_samples, exc_samples = [], []
      n = 0
      while True:
        n += 1
        if n > 100:
          #print(vm, "failed to achieve precision")
          break
        sh_samples.append(choice(shared))
        exc_samples.append(choice(exclusive))
        cur = mean(sh_samples)/mean(exc_samples)
        if abs(1-cur/true) < 1-thr:
          nums.append(n)
          break
    m = mean(nums)
    d = pstdev(nums)
    rd = d/m*100
    print("{vm}: {m:.1f} {rd:.1f}%".format(vm=vm, m=m,d=d,rd=rd))
    result[vm]=mean(nums)
  #print("RESULT for thr=%s:" % thr, result)

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
    params = parse(plot)
    print(params)
    funcname = params.pop('func')
    func = globals()[funcname]
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
    if args.show: p.show()
