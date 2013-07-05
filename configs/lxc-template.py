#!/usr/bin/env python3
import argparse
from libvmc import gen_mac
import sys

TPL = """
lxc.utsname = {name}
lxc.rootfs = {root}

lxc.network.type = veth
lxc.network.flags = up
lxc.network.link = intbr
lxc.network.hwaddr = {mac}
lxc.network.ipv4 = {addr}
lxc.network.name = eth0
lxc.network.ipv4.gateway = {gw}

lxc.autodev = 1
lxc.cap.drop = mknod
lxc.tty = 4
lxc.pts = 1024
"""


def main():
  parser = argparse.ArgumentParser(description='Create template')
  parser.add_argument('--path', required=True, help="path to store config")
  parser.add_argument('--name', required=True, help="container name")
  parser.add_argument('--root', required=True, help="rootfs location")
  parser.add_argument('--mac', default="random", help="mac address")
  parser.add_argument('--gw', default="172.16.5.1", help="default gaeway")
  parser.add_argument('--addr', default="172.16.5.10/24", help="ipv4 address")
  args = parser.parse_args()
  print("passed args:", args)
  if args.mac == 'random':
    args.mac = gen_mac()
    print(args.mac)
  with open(args.path+"/config", 'w') as fd:
    cfg = TPL.format(**vars(args))
    fd.write(cfg)

if __name__ == '__main__':
  main()
