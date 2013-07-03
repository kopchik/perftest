#!/usr/bin/env python3
from socket import gethostname
from useful.mstring import s
from subprocess import *
from useful.run import *
import os.path
import atexit
import shlex
import time
import os


HOSTNAME = gethostname()
if HOSTNAME == "ux32vd":
  PREFIX = "/mnt/btrfs/"
elif HOSTNAME == "u2":
  PREFIX = "/home"
else:
  raise Exception("Unknown host. Please add configuration for it.")


class LXC:
  def __init__(self, name, path, tpl):
    self.name = name
    self.path = path
    self.tpl = tpl
    self.started = False
    self.destroy()
    tpl_path = "/home/exe/github/kvmtests/arm/configs/lxc-template.py"
    sudo(s("btrfs subvolume snapshot ${tpl} ${path}"))
    sudo(s("lxc-create -t ${tpl_path} -n ${name} -- --root ${path}"))

  def start(self):
    if self.started:
      return
    sudo(s("lxc-start -n ${self.name} -d"))

  def stop(self, t=10):
    sudo_(s("lxc-shutdown -n ${self.name} -t ${t}"))

  def destroy(self):
    self.stop(t=1)
    sudo_(s("lxc-destroy -n {self.name}"))
    if os.path.exists(self.path):
      sudo(s("btrfs subvolume delete ${self.path}"))


if __name__ == '__main__':
  lxc = LXC(name="perf0", path="/mnt/btrfs/perf0/", tpl="/mnt/btrfs/perftemplate/")
  lxc.start()
  time.sleep(100)
  lxc.stop()
