#!/usr/bin/env python3

from .perftool import stat, NotCountedError
from .slave import MyPopen
from useful.run import sudo, sudo_
from useful.mstring import s
from signal import SIGSTOP, SIGCONT


vms = []
class Bare:
  def __init__(self, cpus):
    assert len(cpus) == 1, "I support only one CPU :("
    self.cpus = cpus
    self.pipe = None
    vms.append(self)

  def create(self):
    pass

  def destroy(self):
    self.pipe.killall()

  def start(self):
    return self.Popen(self.cmd)

  def stop(self):
    if self.pipe:
      self.pipe.killall()
      self.pipe = None

  def shared(self):
    for vm in vms:
      if vm == self: continue
      vm.unfreeze()

  def exclusive(self):
    for vm in vms:
      if vm == self: continue
      vm.freeze()

  def freeze(self):
    assert self.pipe
    self.pipe.killall(SIGSTOP)

  def unfreeze(self):
    assert self.pipe
    self.pipe.killall(SIGCONT)

  def Popen(self, *args, **kwargs):
    self.pipe = MyPopen(*args, **kwargs)
    return self.pipe

  def ipcstat(self, time):
    assert self.pipe
    try:
      r = stat(self.pipe.pid, events=['instructions', 'cycles'], time=time)
      ins = r['instructions']
      cycles = r['cycles']
    except Exception as err:
      raise NotCountedError(err)
    if ins == 0 or cycles == 0:
      raise NotCountedError
    return ins/cycles

  def __repr__(self):
    cls = self.__class__.__name__
    return "{cls}({self.name}, cmd={self.cmd}, cpus=\"{self.cpus}\")".format(cls=cls, self=self)
