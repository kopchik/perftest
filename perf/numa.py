#!/usr/bin/env python3
from .utils import read_val, read_int, str2list
from .utils import run
import os

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


# TODO: assert only one-node is supported
class CPUTopology:
  """ Get NUMA topology. Only online CPUs are counted. """
  cpus = []
  cpus_no_ht = []
  ht_siblings = {}

  def get_thread_sibling(self, cpu):
    siblings = read_int_list(PREFIX + "cpu/cpu%s/topology/thread_siblings_list" % cpu)
    siblings.remove(cpu)
    return siblings

  def __init__(self):
    self.cpus  = read_int_list(PREFIX + "cpu/online")
    self.ht_siblings = {}
    for cpu in self.cpus:
      self.ht_siblings[cpu] = self.get_thread_sibling(cpu)
    self.cpus_no_ht = filter_ht(self.cpus)

  def __str__(self):
    return "All cpus: {cpus}\n" \
    "Without HT: {noht}\nHyper-Threading map: {htmap}"\
    .format(cpus=self.cpus, noht=self.cpus_no_ht, htmap=self.ht_siblings.items())
topology = CPUTopology()


if __name__ == '__main__':
  print(topology)
