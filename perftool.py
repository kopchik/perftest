#!/usr/bin/env python3

from subprocess import *
from useful.log import log
import os

os.environ["PERF_PAGER"]="cat"
log = Log("perftool")

counters_cmd = """perf list %s --no-pager |  grep -v 'List of' | awk '{print $1}' |  grep -v '^$'"""
def get_events(hw=True, sw=True, cache=True, tracepoint=True):
  selector = ""
  if hw: selector += " hw"
  if sw: selector += " sw"
  if cache: selector += " cache"
  if tracepoint: selector += " tracepoint"

  cmd = counters_cmd % selector
  raw = check_output(cmd, shell=True)
  return raw.decode().strip(' \n').split('\n')

def stat(pid, events, t):
  evcmd = ",".join(events)
  cmd = "sudo perf stat -e {events} --log-fd 1 -x, -p {pid}".format(events=evcmd, pid=pid)
  p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
  time.sleep(t)
  check_output("sudo kill -INT %s" % p.pid)
  raw_data = p.stdout.readall()
  log.notice(raw_data)


if __name__ == '__main__':
  print(get_events())
  measure(pid=1,t=1)