#!/usr/bin/env python3
from useful.log import Log
from .utils import read_val, read_int, str2list
from .utils import run
import os

log = Log(['perf','numa'])

PREFIX = "/sys/devices/system/"


def read_int_list(path):
  return str2list(read_val(path))


def get_online_nodes():
  return read_int_list(PREFIX + "node/online")


def get_cpu_name():
  cpus_raw = run("cat /proc/cpuinfo | grep 'model name' | cut -d' ' -f3-", shell=True)
  cpus = set([item.strip() for item in cpus_raw.split('\n') if item])
  assert len(cpus) == 1, "Omg, different CPUs installed in this machine??"
  return cpus.pop()


def filter_ht(cpus: list):
  virtuals = set()
  for cpu in cpus:
    siblings = read_int_list(PREFIX + "cpu/cpu%s/topology/thread_siblings_list" % cpu)
    assert len(siblings) == 1 or len(siblings) == 2, \
      "Hmm... Hyper-Threading with more than two siblings??"
    if len(siblings) == 2:
      virtuals.add(siblings[1])
  return list( filter(lambda c: c not in virtuals, cpus) )


def cpus2mask(cpus):
  mask = 0x0
  for cpu in cpus:
    mask |= 1 << cpu
  return mask


def mask2cpus(mask):
  cpus = []
  i = 0
  while mask:
    if mask & 1:
      cpus.append(i)
    i += 1
    mask = mask >> 1
  return cpus


def get_cur_cpu(pid):
  cmd = "ps h -p %s -o psr" % pid
  rawcpu = run(cmd)
  return int(rawcpu)


def pin_task(pid, cpu):
  mask = cpus2mask([cpu])
  return set_affinity(pid, mask)

def get_affinity(pid):
  cmd = "schedtool %s" % pid
  raw = run(cmd)
  rawmask = raw.rsplit(b'AFFINITY')[1]
  return int(rawmask, base=16)


def set_affinity(pid, mask):
  cmd = "taskset -ap %s %s" % (hex(mask), pid)
  run(cmd, sudo='root')


# TODO: assert only one-node is supported
class CPUTopology:
  """ Get NUMA topology. Only online CPUs are counted. """

  def __init__(self):
    self.all  = read_int_list(PREFIX + "cpu/online")
    self.ht_map = {}
    for cpu in self.all:
      self.ht_map[cpu] = self.get_thread_sibling(cpu)
    self.no_ht = filter_ht(self.all)
    ht = list(set(self.all) - set(self.no_ht))
    self.by_rank = sorted(self.no_ht) + sorted(ht)

  def get_thread_sibling(self, cpu):
    siblings = read_int_list(PREFIX + "cpu/cpu%s/topology/thread_siblings_list" % cpu)
    siblings.remove(cpu)
    return siblings

  def __str__(self):
    return "All cpus: {cpus}\n" \
    "Without HT: {noht}\n" \
    "Hyper-Threading map: {htmap}\n" \
    "Ranked: {rank}\n" \
    .format(cpus=self.all, noht=self.no_ht, htmap=self.ht_map.items(), rank=self.by_rank)
topology = CPUTopology()


if __name__ == '__main__':
  log.info(topology)
