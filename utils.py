#!/usr/bin/env python3
from useful.typecheck import type_check
import subprocess
import shlex
import os


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


if __name__ == '__main__':
  print(str2list("1,2,7-9"))
