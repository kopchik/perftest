#!/usr/bin/env python3
from plotter import stability
import argparse




if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-o', '--output', default=None, help="where to save image")
  parser.add_argument('--show', action='store_const', const=True, default=False, help="show plot?")
  parser.add_argument('--title', default=None)
  parser.add_argument('-a', '--annotations', default=None, nargs='+')
  parser.add_argument('-f', '--files', nargs='+', required=True)
  args = parser.parse_args()
  stability(args.files, show=args.show, output=args.output)