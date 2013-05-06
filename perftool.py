#!/usr/bin/env python3

from collections import OrderedDict
from useful.log import Log
from subprocess import *
import termios
import struct
import fcntl
import shlex
import time
import pty
import os


counters_cmd = """perf list %s --no-pager |  grep -v 'List of' | awk '{print $1}' | grep -v '^$'"""
NOT_SUPPORTED = '<not supported>'
NOT_COUNTED = '<not counted>'
os.environ["PERF_PAGER"]="cat"
log = Log("perftool")
BUF_SIZE = 65535


def get_events(hw=True, sw=True, cache=True, tp=True):
  selector = ""
  if hw: selector += " hw"
  if sw: selector += " sw"
  if cache: selector += " cache"
  if tp: selector += " tracepoint"

  cmd = counters_cmd % selector
  raw = check_output(cmd, shell=True)
  return raw.decode().strip(' \n').split('\n')


def get_useful_events():
  """select counters that are the most useful for our purposes"""

  bad = "kvmmmu:kvm_mmu_get_page,kvmmmu:kvm_mmu_sync_page,kvmmmu:kvm_mmu_unsync_page,,kvmmmu:kvm_mmu_prepare_zap_page".split(',')
  result =  get_events(hw=True, sw=True, tp=False)
  tpevents = get_events(tp=True)
  for prefix in ['kvm:', 'kvmmmu:', 'vmscan:', 'irq:']:
    result += filter(lambda ev: ev.startswith(prefix), tpevents)
  result = filter(lambda x: x not in bad, result)
  return list(result)


def osexec(cmd):
  cmd = shlex.split(cmd)
  os.execlp(cmd[0], *cmd)


def stat(pid, events, t, ann=None, norm=False):
  evcmd = ",".join(events)
  cmd = "sudo perf stat -e {events} --log-fd 1 -x, -p {pid}".format(events=evcmd, pid=pid)
  pid, fd = pty.fork()
  if pid == 0:
    osexec(cmd)
  # fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("hhhh", 24, 80, 0, 0)) # resise terminal

  #disable echo
  flags = termios.tcgetattr(fd)
  flags[3] &= ~termios.ECHO
  termios.tcsetattr(fd, termios.TCSADRAIN, flags)

  time.sleep(t)
  ctrl_c = termios.tcgetattr(fd)[-1][termios.VINTR]  # get Ctrl+C character
  os.write(fd, ctrl_c)
  os.waitpid(pid, 0)
  raw = os.read(fd, BUF_SIZE)
  assert len(raw) < BUF_SIZE, "buffer full on read"
  return PerfData(raw, ann=ann, norm=norm)


class PerfData(OrderedDict):
  def __init__(self, rawdata, ann=None, norm=False):
    super().__init__()
    self.ann  = ann   #annotation
    self.norm = norm

    array = rawdata.decode().split('\r\n')
    # skipping preamble
    if array[0].startswith("#"):
      preamble = array.pop(0)
    # skip empty lines and warnings
    for x in array:
      if not x or x.find('Warning:') != -1:
        array.remove(x)
    assert 'Not all events could be opened.' not in array
    # convert raw values to int or float
    array = map(lambda x: x.split(','), array)
    for raw_value, key in array:
      if raw_value == NOT_SUPPORTED:
        value = False
      elif raw_value == NOT_COUNTED:
        value = None
      else:
        if raw_value.find('.') != -1:
          value = float(raw_value)
        else:
          value = int(raw_value)
      self[key] = value
    # ensure common data layout
    if self.get('cycles', None):
      self['cpu-cycles'] = self['cycles']
    elif self.get('cpu-cycles', None):
      self['cycles'] = self['cpu-cycles']
    #calculate instructions per cycle (inpc)
    inpc = None
    if self.get('cycles', None) and self.get('instructions', None):
      cycles = self['cycles']
      instructions = self['instructions']
      if isinstance(cycles, int) and isinstance(instructions, int):
        inpc = instructions / cycles
    self['_inpc_'] = inpc
    # normalize values if requested
    if self.norm:
      assert 'cycles' in self, "norm=True needs cycles to be measured"
      cycles = self['cycles']
      for k, v in self.items():
        if isinstance(v, (int,float)):
          self[k] = v/cycles


  def normalized(self):
    if self.norm:
      return self
    assert 'cycles' in self, "no cycles counter"
    new_dict = OrderedDict()
    cycles = self['cycles']
    for key, value in self.items():
      if key == '_inpc_':  # instructions-per-cycle is already normalized
        new_dict[key] = value
      if isinstance(value, (int,float)):
        new_dict[key] = value/cycles
      else:
        new_dict[key] = value
    return new_dict


  def __repr__(self):
    result = []
    if self.ann:
      result += ["ann=%s"%self.ann]
    if self.norm:
      result += ["norm=True"]
    result += ["%s=%.4s"%(k,v) for k,v in self.items()]
    return "Perf(%s)" % (", ".join(result))


    # inpc = self['_inpc_']
    # if isinstance(inpc, float):
    #   return "Perf(inpc={:.2f})".format(self['_inpc_'])
    # else:
    #   return super().__repr__()


def pperf(perf):
  """pretty perf data printer"""
  cycles = perf['cycles']
  for key, value in perf.items():
    if isinstance(value, int):
      print(key, ":", value/cycles)
    else:
      print(key, value)


def pidof(psname, exact=False):
  psname = psname

  pids = (pid for pid in os.listdir('/proc') if pid.isdigit())
  result = []
  for pid in pids:
    name, *cmd = open(os.path.join('/proc', pid, 'cmdline'), 'rt').read().strip('\x00').split('\x00')
    if exact:
      if name == psname:
        result += [pid]
    else:
      if name.startswith(psname):
        result += [pid]
  if not result:
    raise Exception("no such process: %s (exact=%s)" % (psname, exact))
  return result


if __name__ == '__main__':
  # print("You got the following counters in your CPU:\n",
  #   get_events())
  print("making stats on own pid...")
  r = stat(pid=os.getpid(), events=get_useful_events(), t=0.5, norm=True)
  print(r)
