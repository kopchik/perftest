#!/usr/bin/env python3
# http://lwn.net/Articles/421574/
from useful.typecheck import TypeCheck
from utils import run, cpu_count
from perf import IPC
import signal
import shlex
import numa
import os

# WARNING WARNING WARNING
# we assume that this library takes full control
# over cgroups it manages. It does not have many
# sanity checks. This is by design

SIGNAMES = dict((k, v) for v, k in signal.__dict__.items() if v.startswith('SIG'))

prefix = "/sys/fs/cgroup"
MAXCPUS = cpu_count()
CPUMASK = 2 ** MAXCPUS - 1
assert TypeCheck  # to suppress flake8 wrong warning


def list_cgroups():
  cmd = "lscgroup | cut -d: -f2 | grep -v '/system' | sort | uniq"
  raw = run(cmd)
  return raw.split('\n')[:-1]


class CGroup(metaclass=TypeCheck):
  def __init__(self, path: str=None, **kwargs):
    super().__init__(**kwargs)
    assert path
    self.path = path
    self.subsystems = []

  def exec(self, cmd, **kwargs):
    if isinstance(cmd, str):
      cmd = shlex.split(cmd)
    params = ",".join(self.subsystems) + ":" + self.path
    return run(["cgexec", "-g", params] + cmd, **kwargs)

  def killall(self, sig=signal.SIGTERM):
    #TODO: freeze
    for pid in self.get_pids():
      #print("killing %s with %s" % (pid, SIGNAMES[sig]))
      os.kill(pid, sig)

  def waitall(self, timeout=False, killem=False):
    if killem and timeout is False:
      raise Exception("Wrong arguments")

    if timeout is not False:
      assert timeout > 0, "timeout should be positive"

    if timeout:
      signal.signal(signal.SIGALRM, lambda x,y: None)
      signal.setitimer(0, timeout, signal.ITIMER_REAL)

    interrupted = False
    for pid in self.get_pids():
      try:
        #print("waiting", pid)
        os.waitpid(pid, 0)
        #print("pid", pid, "gone")
      except ChildProcessError:
        pass
      except InterruptedError:
        # ALARM raised
        interrupted = True
        if killem:
          self.killall(sig=signal.SIGKILL)
          return self.waitall(timeout=10)  # again wait till all processes will die
        raise Exception("timeout")
    else:
      # All stopped
      if timeout:
        signal.setitimer(0, 0, signal.ITIMER_REAL)  # disable timer

  def add_pid(self, pid):
    for subsys in self.subsystems:
      fullpath = prefix + "/" + subsys + "/" + self.path
      with open(fullpath + "/tasks", "a") as fd:
        fd.write(str(pid))

  def get_pids(self):
    subsys = self.subsystems[0]  # we assume that all subsystems have the same tasks
    fullpath = prefix + "/" + subsys + "/" + self.path
    with open(fullpath + "/tasks") as fd:
      return [int(pid) for pid in fd]

  def join_subsys(self, name: str):
    self.subsystems += [name]
    return run("cgcreate -g {name}:{path}"
               .format(name=name, path=self.path), sudo="root")

  def leave_subsys(self):
    for subsys in self.subsystems:
      run("cgdelete -g {subsys}:{path}"
          .format(subsys=subsys, path=self.path))

  def get_value(self, name: str):
    #TODO: check this
    raw = run("cgget -n -v -r %s %s" % (name, self.path))
    return raw.strip()

  def get_int(self, name: str):
    return int(self.get_value(name))

  def set_value(self, name: str, value: str):
    subsys = name.split('.')[0]
    with open(prefix + '/' + subsys + self.path + '/' + name, "w") as fd:
      fd.write(value)
    #return run("cgset -r %s=%s %s" % (name, value, self.path), sudo="root")

  def set_int(self, name: str, value: int):
    return self.set_value(name, str(value))


class Memory(CGroup):
  def __init__(self, swappiness: int=None, memlimit: int=None, **kwargs):
    super().__init__(**kwargs)
    self.join_subsys("memory")
    if swappiness is not None:
      self.set_swappiness(swappiness)
    if memlimit is not None:
      self.set_memlimit(memlimit)

  def set_swappiness(self, swappiness):
    self.set_int("memory.swappiness", swappiness)

  def set_memlimit(self, value):
    """Set hard memory limit in megs"""
    value = value * 1024 * 1024
    self.set_int("memory.limit_in_bytes", value)


class CPU(CGroup):
  def __init__(self, cpushare: int=None, **kwargs):
    super().__init__(**kwargs)
    self.join_subsys("cpu")
    if cpushare is not None:
      self.set_cpushare(cpushare)

  def set_cpushare(self, share: int):
      """set cpu share in percents"""
      assert share in range(0, 101)
      period = self.get_int("cpu.cfs_period_us")
      if share == 100:
        share = -1  # -1 means no cpu bandwidth restrictions
      else:
        share = int(period * share / 100)
      self.set_int("cpu.cfs_quota_us", share)

  def get_cpushare(self):
    period = self.get_int("cpu.cfs_period_us")
    quota = self.get_int("cpu.cfs_quota_us")
    if quota == -1:
      return 100
    return int(quota / period * 100)


class CPUSet(CGroup):
  def __init__(self, cpus: list=None, **kwargs):
    super().__init__(**kwargs)
    self.join_subsys("cpuset")
    nodes = numa.get_online_nodes()
    nodes = ",".join(map(str, nodes))
    self.set_value("cpuset.mems", nodes)
    if cpus is not None:
      self.set_cpus(cpus)

  #TODO: check if it does not exceed maxcpu
  def set_cpus(self, cpus: list):
    #nodes = set()
    cpus = ",".join(map(str, cpus))
    self.set_value("cpuset.cpus", cpus)

  def get_cpus(self)->list:
    result = []
    raw = self.get_value("cpuset.cpus")
    if not raw:
      return list(range(MAXCPUS))  # TODO: check this
    for x in raw.split(","):
      if x.isnumeric():
        result.append(int(x))
      else:
        a, b = map(int, x.split('-'))
        result += range(a, b + 1)
      return result


class PerfEvent(CGroup):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.join_subsys("perf_event")
    self.ipc = None

  def enable_ipc(self):
    if self.ipc:
      return print("IPC already enabled")
    cpus = self.get_cpus()
    assert len(cpus) == 1, "multiple cpus are not supported"
    cpu = cpus[0]
    self.ipc = IPC(self.path, cpu)

  def disable_ipc(self):
    if not self.ipc:
      return print("IPC isn't enabled or already disabled")
    self.ipc.close()
    self.ipc = None
    pass  # TODO

  def get_ipc(self, reset=False):
    return self.ipc.read(reset=reset)


if __name__ == '__main__':
  import unittest
  import time

  class MyCG(Memory, CPUSet, CPU, PerfEvent):
    pass

  matrix_cmd = "bencher.py -q -w 1 -s 1000 " \
               "-- /home/exe/repos/utilz/cputests/matrix.py 1024 1"
  # cg = MyCG(path="/crm", cpus=[0])
  # cg.enable_ipc()
  # cg.exec(matrix_cmd, bg=True)

  # cg2 = MyCG(path="/crm2", cpus=[1])
  # cg.exec(matrix_cmd, bg=True)

  # while True:
  #   print(cg.get_ipc(reset=True))
  #   time.sleep(1)
  # # print(cg.get_cpus())  # TODO: raises exception if cpuset.cpus is empty

  class Test(unittest.TestCase):
    def setUp(self):
      self.cg = MyCG(path="/test", cpus=[0])
      self.cg.killall(sig=signal.SIGKILL)

    def tearDown(self):
      self.cg.waitall(timeout=0.1, killem=True)
      self.cg.leave_subsys()

    def test_spawn_kill(self):
      self.cg.exec("burnP6", bg=True)
      time.sleep(0.5)
      print("I have current pids:", self.cg.get_pids())
      self.cg.waitall(timeout=0.5, killem=True)
      self.assertFalse(self.cg.get_pids())

    def test_ipc(self):
      self.assertFalse(self.cg.get_pids())
      self.cg.enable_ipc()
      time.sleep(0.5)
      assert self.cg.get_ipc(reset=True) == 0.0

      self.cg.exec("burnP6", bg=True)
      time.sleep(0.5)
      ipc = self.cg.get_ipc(reset=False)
      print("IPC:", ipc)
      self.cg.waitall(timeout=0.1, killem=True)
      self.cg.disable_ipc()

    def test_add_pid(self):
      p=run("burnP6", bg=True)
      pid = p.pid
      self.cg.add_pid(pid)
      # print("pids are:", self.cg.get_pids())
      assert pid in self.cg.get_pids()
  unittest.main()
