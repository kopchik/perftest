#!/usr/bin/env python3

from useful.csv import Reader as CSVReader
from useful.log import Log

from .utils import memoized

from collections import OrderedDict
from subprocess import check_call
from socket import socketpair
from signal import SIGTERM
from pprint import pprint
from subprocess import *
import argparse
import shlex
import os


class NotCountedError(Exception):
  pass

counters_cmd = """perf list %s --no-pager |  grep -v 'List of' | awk '{print $1}' | grep -v '^$'"""
NOT_SUPPORTED = '<not supported>'
NOT_COUNTED = '<not counted>'
os.environ["PERF_PAGER"]="cat"
log = Log("perftool")
BUF_SIZE = 65535

def _get_events(hw=True, sw=True, cache=True, tp=True):
  selector = ""
  if hw: selector += " hw"
  if sw: selector += " sw"
  if cache: selector += " cache"
  if tp: selector += " tracepoint"

  cmd = counters_cmd % selector
  raw = check_output(cmd, shell=True)
  return raw.decode().strip(' \n').split('\n')



@memoized('/tmp/get_events.pickle')
def get_events():
  """select counters that are the most useful for our purposes"""

  bad = "kvmmmu:kvm_mmu_get_page,kvmmmu:kvm_mmu_sync_page," \
        "kvmmmu:kvm_mmu_unsync_page,kvmmmu:kvm_mmu_prepare_zap_page".split(',')
  result =  _get_events(tp=False)
  result = ['cycles' if x=='cpu-cycles' else x for x in result]  # replace cpu-cycles with cycles
  #tpevents = get_events(tp=True)
  #for prefix in ['kvm:', 'kvmmmu:', 'vmscan:', 'irq:', 'signal:', 'kmem:', 'power:']:
  #  result += filter(lambda ev: ev.startswith(prefix), tpevents)
  #result = filter(lambda x: x not in bad, result)
  #TODO result += ['irq:*', 'signal:*', 'kmem:*']

  # filter out events that are not supported
  p = Popen(shlex.split('bzip2 -k /dev/urandom -c'), stdout=DEVNULL)
  perf_data = stat(p.pid, result, t=0.5, ann="test run")
  p.send_signal(SIGTERM)
  clean = []
  for k, v in perf_data.items():
    if v is False:
      log.notice("event %s not supported"%k)
      #result.remove(k)
      continue
    elif v is None:
      log.critical("event %s not counted"%k)
      #result.remove(k)
      continue
    clean += [k]
  return clean


def stat(pid=None, events=[], time=0, perf="perf", guest=False, extra=""):
  # parse input
  assert events and time
  CMD = "{perf} kvm" if guest else "{perf}"
  CMD += " stat -e {events} --log-fd {fd} -x, {extra} sleep {time}"
  if pid: extra += " -p %s" % pid
  # prepare cmd and call it
  read, write = socketpair()
  cmd = CMD.format(perf=perf, pid=pid, events=",".join(events), \
                   fd=write.fileno(), time=time, extra=extra)
  check_call(shlex.split(cmd), pass_fds=[write.fileno()])  # TODO: buf overflow??
  result = read.recv(100000).decode()
  # parse output of perf
  r = {}
  for s in result.splitlines():
    rawcnt,_,ev,*_ = s.split(',')
    if rawcnt == '<not counted>':
      raise NotCountedError
    r[ev] = int(rawcnt)
  return r


def kvmstat(*args, **kwargs):
  return stat(*args, guest=True, **kwargs)


def cgstat(*args, path=None, cpus=None, **kwargs):
  assert path and cpus
  extra = "-C {cpus} -G {path}".format(path=path, cpus=",".join(map(lambda x: str(x), cpus)))
  return stat(*args, extra=extra, **kwargs)



if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Run experiments')
  parser.add_argument('-t', '--time', type=float, default=10, help="measurement time")
  parser.add_argument('-e', '--events', default=False, const=True, action='store_const', help="get useful events")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--kvmpid', type=int, help="pid of qemu process")
  group.add_argument('--pid', type=int, help="pid of normal process")
  args = parser.parse_args()
  print(args)

  stat_args = dict(pid=args.pid if args.pid else args.kvmpid, t=args.time, ann="example output", norm=True)
  if args.kvmpid:
    r = kvmstat(events=get_events(), **stat_args)
  elif args.pid:
     r = stat(events=get_events(), **stat_args)
  else:
    r = get_events()
    r = ",".join(r)

  pprint(r)
