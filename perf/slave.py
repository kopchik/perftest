#!/usr/bin/env python3
__VERSION__ = 0.5
from rpyc.utils.server import ThreadedServer  # or ForkingServer
import subprocess
import argparse
from signal import SIGSTOP, SIGKILL
import shlex
import rpyc
import os

from useful.small import partition2


# XXX doesn't work at all
#def handleSIGCHLD(*args, **kwargs):
#    print(args, kwargs)
#    r = os.waitpid(-1, os.WNOHANG)
#    print("dead children:", r)
#signal.signal(signal.SIGCHLD, handleSIGCHLD)
#signal.siginterrupt(signal.SIGCHLD, True)


class MyPopen(subprocess.Popen):
  def __init__(self, cmd, *args, **kwargs):
    # do not split into tokens if shell=True is specified
    # because shell will execute only the first element
    if isinstance(cmd, str) and not kwargs.get('shell', False):
      cmd = shlex.split(cmd)
      env, cmd = partition2(cmd, key=lambda s: s.find('=') > 0)
      env = dict(e.split('=') for e in env)
      print("ENV:", env, "CMD:", cmd)
      if not env:
        env = None
    super().__init__(cmd, *args, env=env, **kwargs)

  def killall(self, sig=SIGKILL):
    if self.poll() is not None:
        return
    #kill children
    self.send_signal(SIGSTOP)
    cmd = "pkill -{sig} -P {pid}".format(sig=sig, pid=self.pid)
    subprocess.call(cmd.split())
    #kill myself
    self.send_signal(sig)


class MyService(rpyc.Service):
  def exposed_Popen(self, *args, **kwargs):
      return MyPopen(*args, **kwargs)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='RPC slave')
  parser.add_argument('--port', type=int, default=6666, help="port to listen")
  args = parser.parse_args()
  print(args)
  server = ThreadedServer(MyService, port=args.port, reuse_addr=True,
                          protocol_config={"allow_all_attrs":True})
  server.start()
