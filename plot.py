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

def single(path, label=None, color=None):
  
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
  p.plot(ts, cycles, label=label, lw=4, **args)


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-o', '--output', default=None, help="where to save image")
  parser.add_argument('--show', action='store_const', const=True, default=False, help="show plot?")
  parser.add_argument('-t', '--title', help="plot title")
  parser.add_argument('-a', '--annotations', default=None, nargs='+')
  parser.add_argument('-x', '--xlabel', default=None)
  parser.add_argument('--xlim', type=int, nargs=2, help="limit X axis of the plot")
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
  if args.show: p.show()
  if args.title: p.title(args.title)
  if args.output:
    p.savefig(args.output, dpi=300, bbox_inches='tight')
