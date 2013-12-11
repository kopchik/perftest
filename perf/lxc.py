#!/usr/bin/env python3

""" Actung! Quick`n`Dirty code, do not use in production
"""
from .perftool import cgstat
from .utils import retry

from useful.run import sudo, sudo_
from useful.mstring import s
from libvmc import gen_mac

from os.path import exists
import rpyc
import os

TPL = """
lxc.utsname = ${self.name}
lxc.rootfs = ${self.root}

lxc.network.type = veth
lxc.network.flags = up
lxc.network.link = intbr
lxc.network.hwaddr = ${self.mac}
lxc.network.ipv4 = ${self.addr}
lxc.network.name = eth0
lxc.network.ipv4.gateway = ${self.gw}

lxc.autodev = 1
lxc.cap.drop = mknod
lxc.tty = 4
lxc.pts = 1024
"""


class LXC:
  def __init__(self, name, root, tpl, addr, gw, cpus=None):
    self.name = name
    self.root = root
    self.addr = addr
    self.gw   = gw
    self.tpl  = tpl
    self.mac  = gen_mac()
    self.started = False
    self.cpus = cpus
    self.rpc  = None

  def create(self):
    if exists(self.root):
      raise Exception(s("Cannot create snapshot: path exists: ${self.root}"))
    sudo(s("btrfs subvolume snapshot ${self.tpl} ${self.root}"))
    os.makedirs(s("/var/lib/lxc/${self.name}/"))
    with open(s("/var/lib/lxc/${self.name}/config"), 'w') as fd:
      data = s(TPL)
      fd.write(data)
      if self.cpus:
        strcpus = ",".join(map(lambda x: str(x), self.cpus))
        fd.write("lxc.cgroup.cpuset.cpus = %s\n" % strcpus)

  def destroy(self):
    self.stop(t=1)
    sudo_(s("lxc-destroy -n ${self.name}"))
    if exists(self.root):
      sudo(s("btrfs subvolume delete ${self.root}"))
      sudo_(s("rm -rf ${self.root}"))

  def start(self):
    #if self.started:
    #  return
    sudo(s("lxc-start -n ${self.name} -d"))

  def stop(self, t=10):
    sudo_(s("lxc-shutdown -n ${self.name} -t ${t}"))

  def Popen(self, *args, **kwargs):
    if not self.rpc:
      self.rpc = retry(rpyc.connect, args=(str(self.addr),), \
                        kwargs={"port":6666}, retries=10)
    return self.rpc.root.Popen(*args, **kwargs)

  def stat(self, outfile):
    from config import MEASURE_TIME, events
    cgstat(path="lxc/"+self.name, cpus=self.cpus, events=events, t=MEASURE_TIME, out=outfile)
