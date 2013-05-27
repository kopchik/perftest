#!/usr/bin/env python3
from subprocess import Popen, PIPE
from socket import socketpair
from collections import OrderedDict
from logging import basicConfig, DEBUG
import shlex
import gc

BUFSIZE = 65535
basicConfig(level=DEBUG)

def parse(raw):
  d = OrderedDict()
  for l in raw.decode().splitlines():
    v,k = l.split(',')
    d[k] = v
  return d


def bench(cmd, cpu=None, evs=None, repeats=1):
  assert cpu is not None and evs, "provide CPU and events"
  if isinstance(evs, (list, tuple)): evs = ",".join(evs)
  me, other = socketpair()
  cmd = "schedtool -a {cpu} -e perf stat -e {evs} -x, --log-fd {fd} -r {repeats} -- {cmd}" \
      .format(cpu=cpu, evs=evs, repeats=repeats, fd=other.fileno(), cmd=cmd)
  print(cmd)
  p = Popen(shlex.split(cmd), stderr=PIPE, pass_fds=[other.fileno()])
  
  r = p.wait()
  assert r == 0, "bad return code %s" % r
  
  raw = me.recv(BUFSIZE)
  assert len(raw) < BUFSIZE, "data truncated"
  return parse(raw)


def main():
  gc.disable()
  print(bench("sleep 0.1", evs="cycles", cpu=0))


if __name__ == '__main__':
  main()