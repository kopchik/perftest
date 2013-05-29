#!/usr/bin/env python3
from subprocess import Popen, PIPE, DEVNULL
from logging import basicConfig, DEBUG
from perftool import get_useful_events
from collections import OrderedDict
from useful.bench import StopWatch
from socket import socketpair
from signal import SIGKILL
import shlex
import time
import sys
import gc
import os


BUFSIZE = 65535
basicConfig(level=DEBUG)


benchmarks = dict(
matrix = "/home/sources/kvmtests/benches/matrix.py -s 1024 -r 1",
# pgbench = "sudo -u postgres pgbench -c 20 -s 10 -T 100000",
# nginx_static = "siege -c 100 -t 666h http://localhost/big_static_file",  # TODO: too CPU consuming,
# wordpress = "siege -c 100 -t 666h http://localhost/",
# TODO: 1s
ffmpeg = "ffmpeg -i /home/sources/hd_thx_amazing_life.m2ts \
            -threads 1 -t 1 -y -strict -2 -loglevel panic \
            -acodec aac -aq 100 \
            -vcodec libx264 -preset fast -crf 22 \
            -f mp4 /dev/null",
sdag  = "/home/sources/test_SDAG/test_sdag -t 5 -q 1000 /home/sources/test_SDAG/dataset.dat",
sdagp = "/home/sources/test_SDAG/test_sdag+ -t 5 -q 1000 /home/sources/test_SDAG/dataset.dat",
blosc = "/home/sources/kvmtests/benches/pyblosc.py -r 100",
)

def parse(raw):
  d = OrderedDict()
  for l in raw.decode().splitlines():
    v,k,*p = l.split(',')
    d[k] = v
  return d


def bench(cmd, cpu=None, evs=None, repeats=1):
  assert cpu is not None and evs, "provide CPU and events"
  if isinstance(evs, (list, tuple)): evs = ",".join(evs)
  me, other = socketpair()
  cmd = "schedtool -a {cpu} -e perf stat -e {evs} -x, --log-fd {fd} -r {repeats} -- {cmd}" \
      .format(cpu=cpu, evs=evs, repeats=repeats, fd=other.fileno(), cmd=cmd)
  print(cmd)
  p = Popen(shlex.split(cmd), stdout=DEVNULL, stderr=DEVNULL, pass_fds=[other.fileno()], start_new_session=True)

  r = p.wait()
  assert r == 0, "bad return code %s" % r

  raw = me.recv(BUFSIZE)
  assert len(raw) < BUFSIZE, "data truncated"
  return parse(raw)


def perf_single(benches, out, evs):
  print(time.ctime(), file=out)
  for n, c in benches.items():
    with StopWatch() as t:
      r = bench(c, evs=evs, cpu=0, repeats=3)
      print(r)
    print(n, t.time, r, file=out)


def perf_double(benches, out, evs):
  for bn, bc in benches.items():
    bcmd = "schedtool -a 1 -e perf stat -r 999999 %s" % bc
    print("launching in BG:", bcmd)
    print("\nlaunching in BG:", bn, file=out)
    bp = Popen(shlex.split(bcmd), stdout=DEVNULL, stderr=DEVNULL,  start_new_session=True)
    time.sleep(3)  # warmup sleeping
    for n, c in benches.items():
      with StopWatch() as t:
        r = bench(c, evs="cycles,instructions", cpu=0, repeats=3)
        print(r)
      assert bp.poll() is None, "background unexpectedly died"
      print(n, t.time, r, file=out)
    os.killpg(bp.pid, SIGKILL)
    bp.wait()
    gc.collect()
    time.sleep(0.5)


def main():
  gc.disable()
  #benchmarks = dict(matrix = "/home/sources/kvmtests/benches/matrix.py -s 512 -r 1")
  #events = "cycles,instructions,task-clock"
  events = get_useful_events()

  out = open("results/raw_results_single", "a")
  perf_single(benchmarks, out=out, evs=events)
  out = open("results/raw_results_double", "a")
  perf_double(benchmarks, out=out, evs=events)

  # perf double
  #out = open("raw_results_with_bg", "a")
  #print(time.ctime(), file=out)


if __name__ == '__main__':
  main()
