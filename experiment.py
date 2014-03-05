#!/usr/bin/env python3


from perftool import stat, get_events
import gc; gc.disable()
import argparse
import rpyc
from config import basis, RESULTS, IDLENESS
from utils import check_idleness, wait_idleness
from subprocess import check_call
import shlex


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Run experiments')
  parser.add_argument('-t', '--time', type=int, default=100, help="measurement time (in ms!)")
  parser.add_argument('-d', '--debug', default=False, const=True, action='store_const', help='enable debug mode')
  parser.add_argument('-p', '--pid', type=int, help="pid of process")
  parser.add_argument('-a', '--addr', help="remote addr")
  parser.add_argument('-i', '--interval', type=int, help="interval between measurements")
  args = parser.parse_args()

  rpc = rpyc.connect(args.addr, port=6666)
  RPopen = rpc.root.Popen
  PERFCMD = "sudo perf stat -I {interval} -e {events} -x, -o {output} sleep {time}"
  for name,cmd in basis.items():
    wait_idleness(IDLENESS)
    print("launching %s (%s)"%(name,cmd))
    if name != "pgbench":
      cmd = "bencher.py -s 100000 -- "+cmd
    p = RPopen(cmd)

    perfcmd = PERFCMD.format(interval=args.interval, events="cycles:G", 
                             output=RESULTS+name, time=args.time)
    check_call(shlex.split(perfcmd))

    assert p.poll() is None, "test unexpectedly terminated"
    p.killall()

  rpc.close()
