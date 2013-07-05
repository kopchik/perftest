#!/usr/bin/env python3
from subprocess import PIPE
from lib.utils import run, retry, wait_idleness
from lib.lxc import LXC
from ipaddress import IPv4Address
from socket import gethostname
import rpyc
import time

HOSTNAME = gethostname()
if HOSTNAME == "ux32vd":
  PREFIX = "/mnt/btrfs/"
elif HOSTNAME in ["odroid", "u2"]:
  PREFIX = "/home/"
else:
  raise Exception("Unknown host. Please add configuration for it.")

lxcs = []
for x in range(4):
  ip = str(IPv4Address("172.16.5.10")+x)
  print(ip)
  name = "perf%s" % x
  lxc = LXC(name=name, root=PREFIX+name, tpl=PREFIX+"/perftemplate/",
            addr=ip, gw="172.16.5.1")
  lxcs += [lxc]
  lxc.destroy()
  lxc.create()
  lxc.start()
print("sleeping for a while...")
time.sleep(1)
for lxc in lxcs:
  rpc = rpyc.connect(lxc.addr, port=6666)
  RPopen = rpc.root.Popen
  p = RPopen("ls /", stdout=PIPE)
  print(p.stdout.read())
  lxc.stop(1)
  lxc.destroy()