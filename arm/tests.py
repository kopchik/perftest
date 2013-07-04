#!/usr/bin/env python3
from ipaddress import IPv4Address
from socket import gethostname
from lxc import LXC


if __name__ == '__main__':
  HOSTNAME = gethostname()
  if HOSTNAME == "ux32vd":
    PREFIX = "/mnt/btrfs/"
  elif HOSTNAME in ["odroid", "u2"]:
    PREFIX = "/home/"
  else:
    raise Exception("Unknown host. Please add configuration for it.")

  lxcs = []
  for x in range(4):
    ip = str(IPv4Address("172.16.5.10")+x) + '/24'
    print(ip)
    name = "perf%s" % x
    lxc = LXC(name=name, root=PREFIX+name, tpl=PREFIX+"/perftemplate/",
              addr="172.16.5.10/24", gw="172.16.5.1")
    lxc.destroy()
    lxc.create()
    # lxc.start()
    lxcs += [lxc]

  # for lxc in lxcs:
  #   lxc.stop()
