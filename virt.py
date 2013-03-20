#!/usr/bin/env python3
from kvmc import KVM, Bridged, Drive, CMD, kvms, main

class Default(KVM):
  mem   = 1024
  cores = 1
  net   = None
  cmd   = "qemu-system-x86_64 --enable-kvm -curses"
  auto  = True
  template = True


for i in range(0,7):
  class MyKVM(Default):
    name = "virt%s" % i
    mem = 2048
    net = [Bridged(ifname="virt%s"%i, model='e1000',
           mac="52:54:91:5E:38:%02x"%i, br="intbr")]
    drives = [Drive("/home/sources/perftests/arch64_perf%s.qcow2"%i, cache="unsafe")]


# to use from another scripts
cmd = CMD(kvms)


# if script is used stand-alone...
if __name__ == '__main__':
  main()