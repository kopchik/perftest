#!/usr/bin/env python3
from kvmc import KVM, Bridged, Drive, Manager, main
from numa import OnlineCPUTopology
import cgroup
numainfo = OnlineCPUTopology()
CPUS = numainfo.cpus

class CG(cgroup.PerfEvent, cgroup.CPUSet):
  pass

class CGManager(Manager):
  def __init__(self, cpus):
    self.cpus = cpus
    self.cgroups = {}
    for cpu in CPUS:
      name = str(cpu)
      self.cgroups[name] = CG(path="/cg%s" % name, cpus=[name])
    super().__init__()

  def start(self, name):
    print("test")
    assert isinstance(name, str), "name should be string"
    inst = self.instances[name]
    cg   = self.cgroups[name]
    pid  = inst.start()
    cg.add_pid(pid)

  def __enter__(self):
    self.stop_all()
    for cpu in self.cpus:
      self.start(str(cpu))

  def __exit__(self, type, value, traceback):
    self.graceful(timeout=30)
cgmgr = CGManager(CPUS)


class Template(KVM):
  mgr   = cgmgr
  name  = "template"
  mem   = 1024
  net   = [Bridged(ifname="template", model='e1000',
         mac="52:54:91:5E:38:BB", br="intbr")]
  drives = [Drive("/home/sources/perftests/arch64_template.qcow2",
            cache="unsafe")]
  auto  = False
template = Template()


for i in CPUS:
  Template(
    name = str(i),
    net = [Bridged(ifname="virt%s"%i, model='e1000',
           mac="52:54:91:5E:38:%02x"%i, br="intbr")],
    drives = [Drive("/home/sources/perftests/arch64_perf%s.qcow2"%i,
              cache="unsafe")])


# if script is used stand-alone...
if __name__ == '__main__':
  main(cgmgr)