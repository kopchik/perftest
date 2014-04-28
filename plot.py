#!/usr/bin/env python3
from useful.csv import Reader as CSVReader
from argparse import ArgumentParser
import pylab as p


def parse(cmd):
  return dict(s.split('=') for s in cmd.split('|'))

def single(path, label=None):
  with open(path) as csvfile:
    instr, cycles = [], []
    cur_cycles = 0
    ts = []
    for t, val, cnt in CSVReader(csvfile, type=(float,int,str)):
      if cnt == 'instructions':
        instr.append(val if not args.freq else val/args.freq)
        ts.append(t)
      else:
        cur_cycles += val
        cycles.append(cur_cycles)
    #assert len(cycles) == len(instr)
  p.plot(ts, instr,label=label)


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-o', '--output', default=None, help="where to save image")
  parser.add_argument('--show', action='store_const', const=True, default=True, help="show plot?")
  parser.add_argument('--title', default=None)
  parser.add_argument('-a', '--annotations', default=None, nargs='+')
  parser.add_argument('-x', '--xlabel', default=None)
  parser.add_argument('--xlim', type=int, nargs=2)
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
  if args.xlabel: p.xlabel(args.xlabel)
  if args.ylabel: p.ylabel(args.ylabel)
  if args.xlim: p.xlim(args.xlim)
  if args.show: p.show()
  if args.output:
    p.savefig(args.output, bbox_inches='tight')
