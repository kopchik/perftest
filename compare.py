#!/usr/bin/env python3
import argparse
from plotter import perfbars

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Analyze data from perf stat.')
  parser.add_argument('-o', '--output', default=None, help="where to save image")
  parser.add_argument('-t', '--threshold', type=float, default=0.05, help="foreground task")
  parser.add_argument('--show', action='store_const', const=True, default=False, help="show plot?")
  parser.add_argument('--title', default=None)
  parser.add_argument('-a', '--annotations', default=None, nargs='+')
  parser.add_argument('-f', '--files', nargs='+')

  args = parser.parse_args()
  print(args)
  perfbars(files=args.files,
           annotations=args.annotations,
           thr=args.threshold,
           _title=args.title,
           _show=args.show,
           output=args.output)