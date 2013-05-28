#!/usr/bin/env python3
from subprocess import Popen, PIPE, DEVNULL
from logging import basicConfig, DEBUG
from perftool import get_useful_events
from collections import OrderedDict
from useful.bench import StopWatch
from socket import socketpair
import shlex
import time
import gc


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
  p = Popen(shlex.split(cmd), stdout=DEVNULL, stderr=DEVNULL, pass_fds=[other.fileno()])
  
  r = p.wait()
  assert r == 0, "bad return code %s" % r
  
  raw = me.recv(BUFSIZE)
  assert len(raw) < BUFSIZE, "data truncated"
  return parse(raw)


def main():
  gc.disable()
  # perf single
  out = open("raw_results", "a")
  print(time.ctime(), file=out)
  for n, c in benchmarks.items():
    with StopWatch() as t:
      print(bench(c, evs="cycles,instructions", cpu=0, repeats=1))
    print(n, t.time, file=out)


if __name__ == '__main__':
  main()