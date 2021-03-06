#!/usr/bin/env python3
from useful.typecheck import type_check
from useful.log import Log
from collections import OrderedDict as odict
import subprocess
import pickle
import shlex
import time
import sys
import os

log = Log("UTILS")

def check_idleness(t=10):
  cmd = "sudo perf stat -a -e cycles --log-fd 1 -x, sleep {t}"
  cycles_raw = subprocess.check_output(cmd.format(t=t), shell=True)
  cycles = int(cycles_raw.decode().split(',')[0])
  return (cycles / t) / 10**6


def wait_idleness(maxbusy=3, t=3):
  warned = False
  time.sleep(0.3)
  while True:
    busy = check_idleness(t=t)
    if busy < maxbusy:
      break
    if not warned:
      log.notice("node is still busy more than %s" % maxbusy)
      warned = True
    print("%.1f"%busy, end=' ')
    sys.stdout.flush()
    time.sleep(1)
  print("it's idle enough")


@type_check
def run(cmd, sudo: str=None, shell=False, bg=False):
  if isinstance(cmd, str) and not shell:
    cmd = shlex.split(cmd)
  if sudo:
    cmd = ["sudo", "-u", sudo] + cmd

  if bg:
    p = subprocess.Popen(cmd)
    return p
  else:
    output = subprocess.check_output(cmd, shell=shell)
    return output.decode()


def read_val(path: str):
  with open(path) as fd:
    r = fd.readline()
  return r


@type_check
def read_int(path: str):
  return int(read_val(path))


@type_check
def write_int(path: str, value: int, create: bool=False):
  mode = "w" if create else "r+"
  with open(path, mode) as fd:
    fd.write(str(value))


def cpu_count():
  return os.sysconf('SC_NPROCESSORS_ONLN')


#TODO this is str2intlist actually
@type_check
def str2list(s: str):
  result = []
  s = s.strip()
  for x in s.split(","):
    if x.isnumeric():
      result.append(int(x))
    else:  # if it is a range like "a-b"
      a, b = map(int, x.split('-'))
      result += range(a, b + 1)
  return result


def str2set(s):
  return set(str2list(s))


def retry(f, args, kwargs, sleep=1, retries=20):
  for x in range(retries):
    try:
      return f(*args, **kwargs)
    except Exception as err:
      log.info("retry: %s" % err)
    time.sleep(sleep)
  else:
    #import pdb; pdb.set_trace()
    raise Exception("ne shmogla")


def csv2dict(f):
  d = odict()
  with open(f) as fd:
    for l in fd.readlines():
      if l.startswith('#') or l.isspace():
        continue
      l = l.strip()
      v,k, *rest = l.split(',')
      if k == 'cpu-cycles':
        k = 'cycles'
      # if k in ['cpu-clock', 'task-clock']: continue
      if v == '<not supported>': continue
      d[k] = int(float(v))
  return d


class memoized:
  def __init__(self, path):
    self.path = path
  def __call__(self, f):
    path = self.path
    def wrapper(*args, **kwargs):
      try:
        return pickle.load(open(path, 'rb'))
      except Exception as e:
        print("cannot unpickle %s:" % path, e)
        result = f(*args, **kwargs)
        try:
          pickle.dump(result, open(path, 'wb'))
        except Exception as e:
          print("cannot pickle %s:" % path, e)
        return result
    return wrapper


if __name__ == '__main__':
  print(str2list("1,2,7-9"))
  print("idleness", check_idleness(t=3))
