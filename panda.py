#!/usr/bin/env python3
from subprocess import Popen, PIPE
from socket import socketpair
import shlex
import gc
BUFSIZE = 65535

def parse(raw):
  TODO

def bench(cmd, cpu=None, evs=None, repeats=1):
  assert cpu is not None and evs, "provide CPU and events"
  if isinstance(evs, (list, tuple)): evs = ",".join(evs)
  s1, s2 = socketpair()
  cmd = "schedtool -a {cpu} -e perf stat -e {evs} -x, --log-fd {fd} -r {repeats} -- {cmd}" \
      .format(cpu=cpu, evs=evs, repeats=repeats, fd=s2.fileno(), cmd=cmd)
  print(cmd)
  p = Popen(shlex.split(cmd), stderr=PIPE, shell=True)
  r = p.wait()
  assert r == 0, "bad return code %s" % r
  data = s2.recv(BUFSIZE)
  assert len(data) < BUFSIZE, "data truncated"
  print(data)

def main():
  gc.disable()
  print(bench("sleep 0.1", evs="cycles", cpu=0))


if __name__ == '__main__':
  main()