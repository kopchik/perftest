#!/usr/bin/env python3
from plotter import *
import argparse




if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-o', '--output', default=None, help="where to save image")
  parser.add_argument('--show', action='store_const', const=True, default=False, help="show plot?")
  parser.add_argument('--title', default=None)
  args = parser.parse_args()
  time_vs_dev(show=args.show,
            output=args.output)
