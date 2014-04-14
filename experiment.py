#!/usr/bin/env python3


from perftool import stat, get_events
import gc; gc.disable()
import argparse
import rpyc
from config import basis, RESULTS, IDLENESS, WARMUP_TIME
from utils import check_idleness, wait_idleness
from subprocess import check_call
from time import sleep
import shlex
import os

PERFCMD = "sudo /home/sources/abs/core/linux/src/linux-3.13/tools/perf/perf stat -I {interval} -e {events} -x, -o {output} -p {pid} sleep {time}"

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Run experiments')
  parser.add_argument('-t', '--time', type=int, default=100, help="measurement time (in ms!)")
  parser.add_argument('-d', '--debug', default=False, const=True, action='store_const', help='enable debug mode')
  parser.add_argument('-p', '--pid', type=int, help="pid of process")
  parser.add_argument('-a', '--addr', help="remote addr")
  parser.add_argument('-i', '--interval', type=int, nargs='+', default=[1000, 10000, 1000], help="Select intervals to plot")
  parser.add_argument('-o', '--outdir', type=str, help="path (prefix) were to save data")
  parser.add_argument('-b', '--benches', nargs='+', default=[], help="Select benches to measure")
  args = parser.parse_args()


  try:
    os.kill(args.pid, 0)
  except ProcessLookupError:
    raise Exception("no such pid: %s" % args.pid)

  rpc = rpyc.connect(args.addr, port=6666)
  RPopen = rpc.root.Popen

  start, stop, step = args.interval
  interval = range(start, stop+1, step)

  for name,cmd in basis.items():
    if name not in args.benches:
      continue
    wait_idleness(IDLENESS)
    print("launching %s"%name)
    if name != "pgbench":
      cmd = "bencher.py -s 100000 -- "+cmd
    p = RPopen(cmd)
    sleep(WARMUP_TIME)

    for i in interval:
      print("%s (%s)" % (i, interval))
      outdir = "%s/%s/" % (args.outdir, i)
      os.path.exists(outdir) or os.makedirs(outdir)
      perfcmd = PERFCMD.format(interval=i, events="instructions:G",
                             output=outdir+name, time=args.time, pid=args.pid)
      check_call(shlex.split(perfcmd))

    assert p.poll() is None, "test unexpectedly terminated"
    p.killall()

  rpc.close()
