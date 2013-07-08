#!/usr/bin/env python3
from ipaddress import IPv4Address
from socket import gethostname

from lib.perftool import cgstat
from lib.lxc import LXC

from benches import benches
from config import *

import rpyc
import time


def main():
  lxcs = []
  for x in range(4):
    ip = str(IPv4Address("172.16.5.10")+x)
    print(ip)
    name = "perf%s" % x
    lxc = LXC(name=name, root=LXC_PREFIX+name, tpl=LXC_PREFIX+"/perftemplate/",
              addr=ip, gw="172.16.5.1")
    lxcs += [lxc]
    lxc.destroy()
    lxc.create()
    lxc.start()

  cgstat(path="lxc/"+lxcs[0].name, events=['cycles'], t=1, out="/tmp/out")
