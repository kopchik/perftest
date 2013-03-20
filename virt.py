#!/usr/bin/env python3
from kvmc import KVM, Bridged, Drive, CMD, kvms, main

class Template(KVM):
  name  = "template"
  mem   = 1024
  net = [Bridged(ifname="template", model='e1000',
         mac="52:54:91:5E:38:BB", br="intbr")]
  drives = [Drive("/home/sources/perftests/arch64_template.qcow2", cache="unsafe")]
  auto  = False

for i in range(0, 8):
  class MyKVM(Template):
    name = str(i)
    net = [Bridged(ifname="virt%s"%i, model='e1000',
           mac="52:54:91:5E:38:%02x"%i, br="intbr")]
    drives = [Drive("/home/sources/perftests/arch64_perf%s.qcow2"%i, cache="unsafe")]

# to use from another scripts
cmd = CMD(kvms)

# if script is used stand-alone...
if __name__ == '__main__':
  main()