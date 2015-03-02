#!/usr/bin/env python3

from libvmc import KVM, Bridged, Drive, main, \
  __version__ as vmc_version
assert vmc_version >= 12, "vmc library is too old"
from .perftool import kvmstat, NotCountedError
from .utils import retry
import rpyc


class Template(KVM):
  cmd    = "qemu-system-x86_64 -enable-kvm -curses"
  name   = "template"
  mem    = 1024
  rpc    = None  # to be filled where rpc.connect is called
  net    = [Bridged(ifname="template", model='e1000',
            mac="52:54:91:5E:38:BB", br="intbr")]
  drives = [Drive("/home/sources/perfvms/template.qcow2",
            cache="unsafe")]
  auto   = True
  rpc    = None
  Popen  = None
  bname  = None  # benchmark name

  def Popen(self, *args, **kwargs):
    if not self.rpc:
      self.rpc = retry(rpyc.connect, args=(str(self.addr),),
                       kwargs={"port": 6666}, retries=10)
    return self.rpc.root.Popen(*args, **kwargs)

  def shared(self):
    for vm in self.mgr.instances.values():
      if vm == self:
        continue
      vm.unfreeze()

  def exclusive(self):
    for vm in self.mgr.instances.values():
      if vm == self:
        continue
      vm.freeze()

  def ipcstat(self, t=1, raw=False):
    try:
      r = kvmstat(self.pid, ['instructions', 'cycles'], t)
      ins = r['instructions']
      cycles = r['cycles']
    except Exception as err:
      raise NotCountedError(err)
    if ins == 0 or cycles == 0:
      raise NotCountedError
    return r if raw else ins/cycles


if __name__ == '__main__':
  template = Template()
  main()
