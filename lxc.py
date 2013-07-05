#!/usr/bin/env python3

from useful.run import sudo, sudo_
from useful.mstring import s
from libvmc import gen_mac
import os.path
import os


def asroot(f):
  def wrapped(f):
    pid = os.fork()
    if pid:
      os.waitpid(pid)
    else:
      os.seteuid(TODO)


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
  def __init__(self, name, root, tpl, addr, gw):
    self.name = name
    self.root = root
    self.addr = addr
    self.gw   = gw
    self.tpl  = tpl
    self.mac  = gen_mac()
    self.started = False

  def create(self):
    if os.path.exists(self.root):
      raise Exception(s("Cannot create snapshot: path exists: ${self.root}"))
    sudo(s("btrfs subvolume snapshot ${self.tpl} ${self.root}"))
    os.makedirs(s("/var/lib/lxc/${self.name}/"))
    with open(s("/var/lib/lxc/${self.name}/config"), 'w') as fd:
      data = s(TPL)
      fd.write(data)

  def destroy(self):
    self.stop(t=1)
    sudo_(s("lxc-destroy -n ${self.name}"))
    if os.path.exists(self.root):
      sudo(s("btrfs subvolume delete ${self.root}"))
      sudo_(s("rm -rf ${self.root}"))

  def start(self):
    #if self.started:
    #  return
    sudo(s("lxc-start -n ${self.name} -d"))

  def stop(self, t=10):
    sudo_(s("lxc-shutdown -n ${self.name} -t ${t}"))
