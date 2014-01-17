#!/usr/bin/env python3

from libvmc import KVM, Bridged, Drive, Manager, main, __version__ as vmc_version
from .numa import OnlineCPUTopology
from ipaddress import ip_address
import lib.cgroup as cgroup

assert vmc_version >= 8, "vmc library is too old"
numainfo = OnlineCPUTopology()
CPUS = numainfo.cpus


# class CG(cgroup.PerfEvent, cgroup.CPUSet):
class CG(cgroup.CPUSet):
  pass


class CGManager(Manager):
  def __init__(self, cpus):
    super().__init__()
    self.cpus = cpus
    self.cgroups = {}
    for cpu in CPUS:
      name = str(cpu)
      self.cgroups[name] = CG(path="/cg%s" % name, cpus=[name])
    self.cgroups["template"] = self.cgroups["0"]  # for template machine

  def start(self, name):
    cg  = self.cgroups[name]
    vm = super().start(name)
    cg.add_pid(vm.pid)
    vm.cg = cg
    return vm

  def started(self):
    return list(filter(lambda x: x.is_running(), self.instances.values()))

  def __enter__(self):
    self.graceful(timeout=30)
    #for cpu in self.cpus:
    #  self.start(str(cpu))

  def __exit__(self, type, value, traceback):
    self.graceful(timeout=30)
cgmgr = CGManager(CPUS)


class Template(KVM):
  mgr    = cgmgr
  #cmd    = "qemu-kvm -curses"
  cmd    = "qemu-system-x86_64 -enable-kvm -curses"
  #cmd    = "/home/sources/aur-mirror/kvm-git/src/qemu-kvm/x86_64-softmmu/qemu-system-x86_64 -curses"
  #cmd    = "/home/sources/qemu-new/x86_64-softmmu/qemu-system-x86_64 -curses"
  name   = "template"
  mem    = 1024
  rpc    = None  # to be filled where rpc.connect is called
  cg     = None  # to be filled by mgr
  net    = [Bridged(ifname="template", model='e1000',
         mac="52:54:91:5E:38:BB", br="intbr")]
  drives = [Drive("/home/sources/perfvms/template.qcow2",
            cache="unsafe")]
  auto   = False
  rpc    = None

  def Popen(self, *args, **kwargs):
    if not self.rpc:
      self.rpc = retry(rpyc.connect, args=(str(vm.addr),), \
                        kwargs={"port":6666}, retries=10)
    return rpc.root.Popen(*args, kwargs)
template = Template()


# if script is used stand-alone...
if __name__ == '__main__':
  main(cgmgr)
