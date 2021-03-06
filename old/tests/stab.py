#!/usr/bin/env python3
from subprocess import *
import argparse
import benches
import time
import gc

import shlex
gc.disable()

CMD = "/usr/bin/time -f %e -o {out} -a {cmd}"

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Run experiments')
  parser.add_argument('-d', '--debug', default=False, const=True, action='store_const', help='enable debug mode')
  parser.add_argument('-r', '--repeat', type=int, default=1002, help="how many times repeat each test")
  parser.add_argument('-s', '--sleep', type=float, default=0.3, help="interval between tests")
  parser.add_argument('-p', '--prefix', required=True, help="file prefix")

  args = parser.parse_args()

  tot = args.repeat * len(benches.single)
  cnt = 0

  for name, cmd in benches.single.items():
    out = "results/{prefix}_{name}".format(prefix=args.prefix, name=name)
    cmd = CMD.format(cmd=cmd, out=out)
    cmd = shlex.split(cmd)
    for x in range(args.repeat):
      cnt += 1
      if args.debug:
        print("runnig %s out of %s: %s" % (cnt, tot, cmd))
      check_call(cmd, stdout=DEVNULL, stderr=DEVNULL)
      if args.sleep: time.sleep(args.sleep)
