#!/usr/bin/env python3

from useful.log import Log
from subprocess import *
import termios
import struct
import fcntl
import shlex
import time
import pty
import os

NOT_SUPPORTED = '<not supported>'
NOT_COUNTED = '<not counted>'
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


def osexec(cmd):
  cmd = shlex.split(cmd)
  os.execlp(cmd[0], *cmd)


def stat(pid, events, t):
  evcmd = ",".join(events)
  cmd = "sudo perf stat -e {events} --log-fd 1 -x, -p {pid}".format(events=evcmd, pid=pid)
  print("!!", cmd)
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
  raw = os.read(fd, 65535)
  return PerfData(raw)


class PerfData(dict):
  def __init__(self, rawdata):
    super().__init__()

    rawdata = rawdata.decode()
    print("!!", rawdata)
    array = rawdata.split('\r\n')
    if array[0].startswith("#"):
      preamble = array.pop(0) #print("skipping preamble")
    array = filter(lambda x: x, array) #filter out empty lines
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

    if self.get('cycles', None):
      self['cpu-cycles'] = self['cycles']
    elif self.get('cpu-cycles', None):
      self['cycles'] = self['cpu-cycles']

    #instructions per cycle
    inpc = None
    if self.get('cycles', None)  and self.get('instructions', None):
      cycles = self['cycles']
      instructions = self['instructions']
      if isinstance(cycles, int) and isinstance(instructions, int):
        inpc = instructions / cycles
    self['_inpc_'] = inpc


  def normalized(self):
    new_dict = {}

    cycles = self['cycles']
    for key, value in self.items():
      if isinstance(value, int):
        new_dict[key] = value/cycles
      else:
        new_dict[key] = value
    return new_dict


  def __repr__(self):
    inpc = self['_inpc_']
    if isinstance(inpc, float):
      return "Perf(inpc={:.2f})".format(self['_inpc_'])
    else:
      return super().__repr__()


def pperf(perf):
  """pretty perf data printer"""
  cycles = perf['cycles']
  for key, value in perf.items():
    if isinstance(value, int):
      print(key, ":", value/cycles)
    else:
      print(key, value)


def pidof(psname, exact=False):
  psname = psname.encode()

  pids = (pid for pid in os.listdir('/proc') if pid.isdigit())
  result = []
  for pid in pids:
    name, *cmd = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read().strip(b'\x00').split(b'\x00')
    if exact:
      if name == psname:
        result += [pid]
    else:
      if name.startswith(psname):
        result += [pid]
  return result


if __name__ == '__main__':
  # print("You got the following counters in your CPU:\n",
  #   get_events())
  r = stat(pid=pidof("X"), events=get_events(), t=0.2)
  print(r)