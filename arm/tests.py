#!/usr/bin/env python3
from socket import gethostname
from useful.mstring import s
from subprocess import *
from useful.run import *
from ipaddress import IPv4Address
import os.path
import atexit
import shlex
import time
import os


HOSTNAME = gethostname()
if HOSTNAME == "ux32vd":
  PREFIX = "/mnt/btrfs/"
elif HOSTNAME in ["odroid", "u2"]:
  PREFIX = "/home"
else:
  raise Exception("Unknown host. Please add configuration for it.")


class LXC:
  def __init__(self, name, path, tpl, addr):
    self.name = name
    self.path = path
    self.tpl = tpl
    self.started = False

  def create(self):
    #lxc_tpl = "/home/exe/github/kvmtests/arm/configs/lxc-template.py"
    lxc_tpl = "/home/sources/kvmtests/arm/configs/lxc-template.py"
    if os.path.exists(path):
      raise Exception(s("Cannot create snapshot: path exists: ${self.path}"))
    sudo(s("btrfs subvolume snapshot ${self.tpl} ${self.path}"))
    sudo(s("lxc-create -t ${lxc_tpl} -n ${self.name} -- --root ${self.path} --addr=${self.addr}"))

  def destroy(self):
    self.stop(t=1)
    sudo_(s("lxc-destroy -n ${self.name}"))
    if os.path.exists(self.path):
      sudo(s("btrfs subvolume delete ${self.path}"))
      sudo_(s("rm -rf ${self.path}"))

  def start(self):
    if self.started:
      return
    sudo(s("lxc-start -n ${self.name} -d"))

  def stop(self, t=10):
    sudo_(s("lxc-shutdown -n ${self.name} -t ${t}"))


if __name__ == '__main__':
  lxcs = []
  for x in range(4):
    ip = str (IPv4Address("172.16.5.10")+x) + '/24'
    print(ip)
    lxc = LXC(name="perf0", path=PREFIX+"/perf0/", tpl=PREFIX+"/perftemplate/", addr="172.16.5.10/24")
    lxc.destroy()
    lxc.create()
    lxc.start()
    lxcs += [lxc]

  for lxc in lxcs: lxc.stop()
