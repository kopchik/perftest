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


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Run experiments')
  parser.add_argument('-t', '--time', type=int, default=100, help="measurement time (in ms!)")
  parser.add_argument('-d', '--debug', default=False, const=True, action='store_const', help='enable debug mode')
  parser.add_argument('-p', '--pid', type=int, help="pid of process")
  parser.add_argument('-a', '--addr', help="remote addr")
  parser.add_argument('-i', '--interval', type=int, help="interval between measurements")
  parser.add_argument('-o', '--output', type=str, help="path were to save data")
  args = parser.parse_args()


  try:
    os.kill(args.pid, 0)
  except ProcessLookupError:
    raise Exception("no such pid: %s" % args.pid)

  rpc = rpyc.connect(args.addr, port=6666)
  RPopen = rpc.root.Popen
  PERFCMD = "sudo /home/sources/abs/core/linux/src/linux-3.13/tools/perf/perf stat -I {interval} -e {events} -x, -o {output} -p {pid} sleep {time}"
  for name,cmd in basis.items():
    wait_idleness(IDLENESS)
    print("launching %s"%name)
    if name != "pgbench":
      cmd = "bencher.py -s 100000 -- "+cmd
    p = RPopen(cmd)
    sleep(WARMUP_TIME)

    perfcmd = PERFCMD.format(interval=args.interval, events="cycles:G",
                             output=args.output+'/'+name, time=args.time, pid=args.pid)
    check_call(shlex.split(perfcmd))

    assert p.poll() is None, "test unexpectedly terminated"
    p.killall()

  rpc.close()
