#!/usr/bin/env python3

# from typecheck import CheckTypes
from ctypes import CDLL, Structure, byref, get_errno, \
    c_char_p, c_int, c_uint64, c_void_p


perflib = CDLL("./build/libperf_api.so", use_errno=True)
perflib.cgev_create.argtypes = [c_char_p, c_char_p, c_int]
perflib.restype = c_void_p
MAXNUM = 10


class Result(Structure):
  _fields_ = [
      ("nr", c_uint64),
      ("time_enabled", c_uint64),
      ("time_running", c_uint64),
      ("values", c_uint64 * MAXNUM),
  ]


class CGEvent(Structure):
  _fields_ = [
      ("nr", c_int),
      ("fds", c_int * MAXNUM),
      ("result_size", c_int),
      ("result", Result)
  ]

  def __new__(cls, path: str, events: str, cpu: int):
    if not path.startswith("/sys/fs/cgroup"):
      path = "/sys/fs/cgroup/perf_event" + path
    r = perflib.cgev_create(bytes(path, 'utf8'), bytes(events, 'utf8'), cpu)
    if not r:
      raise IOError(get_errno(), "can't create cgroup")  # TODO: OSError?
    self = CGEvent.from_address(r)
    self._ref = byref(self)
    self._opened = True
    return self

  def read(self, reset=False):
    assert self._opened, "operation on closed descriptors"
    perflib.cgev_read(self._ref)
    if reset:
      self.reset()

  def reset(self):
    assert self._opened, "operation on closed descriptors"
    perflib.cgev_reset(self._ref)

  def close(self):
    if not self._opened:
      return print("operation on closed descriptors")
    perflib.cgev_destroy(self._ref)
    self._opened = False


class IPC:
  def __init__(self, path: str=None, cpu: int=None):
    self.cgev = CGEvent(path=path, events="instructions,cycles", cpu=cpu)

  def read(self, reset=False):
    self.cgev.read(reset=reset)
    instructions = self.cgev.result.values[0]
    cycles = self.cgev.result.values[1]
    return (instructions / cycles) if cycles else 0.0

  def close(self):
    self.cgev.close()


if __name__ == '__main__':
  import time

  # cgev = CGEvent(path="/crm", events="cycles", cpu=0)
  # while True:
  #   cgev.read(reset=True)
  #   print(cgev.result.values[0])
  # time.sleep(1)

  ipc = IPC(path="/crm", cpu=0)
  while True:
    print(ipc.read(reset=True))
    time.sleep(1)