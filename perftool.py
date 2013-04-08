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
  log.info(cmd)
  pid, fd = pty.fork()
  if pid == 0:
    osexec(cmd)
  ## resise terminal
  # fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("hhhh", 24, 80, 0, 0))
  
  #disable echo
  flags = termios.tcgetattr(fd)
  flags[3] &= ~termios.ECHO
  termios.tcsetattr(fd, termios.TCSADRAIN, flags)

  time.sleep(t)
  ctrl_c = termios.tcgetattr(fd)[-1][termios.VINTR]  # get Ctrl+C character
  os.write(fd, ctrl_c)
  os.waitpid(pid, 0)  
  raw_data = os.read(fd, 65535)
  return raw_data.decode()


if __name__ == '__main__':
  print("You got the following counters in your CPU:\n",
    get_events())
  r = stat(pid=534,events=get_events(),t=1)
  print(r)
