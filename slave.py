#!/usr/bin/env python3
__VERSION__ = 0.5
from rpyc.utils.server import ThreadedServer  # or ForkingServer
import subprocess
import argparse
import signal
import shlex
import rpyc
import os


# XXX doesn't work at all
#def handleSIGCHLD(*args, **kwargs):
#    print(args, kwargs)
#    r = os.waitpid(-1, os.WNOHANG)
#    print("dead children:", r)
#signal.signal(signal.SIGCHLD, handleSIGCHLD)
#signal.siginterrupt(signal.SIGCHLD, True)


class MyPopen(subprocess.Popen):
  def killall(self):
    if self.poll() is not None:
        return
    #kill children
    cmd = "pkill -KILL -P %s" % self.pid
    subprocess.call(cmd.split())
    #kill myself
    self.kill()


class MyService(rpyc.Service):
  def exposed_Popen(self, cmd, **kwargs):
    cmd = shlex.split(cmd)
    #p = subprocess.Popen(cmd)
    p = MyPopen(cmd, **kwargs)
    return p


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='RPC slave')
  parser.add_argument('--port', type=int, default=6666, help="port to listen")
  args = parser.parse_args()
  print(args)
  server = ThreadedServer(MyService, port=args.port,reuse_addr=True,
                          protocol_config={"allow_all_attrs":True})
  server.start()