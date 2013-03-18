#!/usr/bin/env python3
from utils import read_val, read_int, str2list
from utils import run
import os

PREFIX = "/sys/devices/system/"


def read_int_list(path):
  return str2list(read_val(path))


def get_online_nodes():
  return read_int_list(PREFIX + "node/online")


def get_cpu_name():
  cpus_raw = run("sudo dmidecode  -s processor-version")
  cpus = set(cpus_raw.strip().split('\n'))
  assert len(cpus) == 1, "Omg, different CPUs installed in this machine??"
  return cpus.pop()

class PC:
  def __init__(self, lvl=0):
    self.lvl = lvl
    self.nodes = []
    for nid in self.get_nodes():
      self.nodes.append(Node(nid, lvl+1))

  def get_nodes(self):
    return read_int_list(PREFIX + "node/online")


class Node:
  id = 0
  def __init__(self, id, lvl):
    self.lvl = lvl
    self.id = id
    self.cpus = []
    for cid in self.get_node_cpus():
      self.cpus.append(CPU(cid, lvl+1))

  def get_node_cpus(self):
    cpus = read_int_list(PREFIX + "node/node%s/cpulist" % self.id)
    return cpus  # TODO: filter only online cpus


class CPU:
  def __init__(self, id, lvl):
    self.id = id
    self.lvl = lvl
    self.cores = []
    for coreid in self.get_cores():
      self.cores.append(Core(coreid, lvl+1))

    def get_cores(self):
      TODO
 
class Core:
  def __init__(self, id, lvl):
    self.id = id
    self.lvl = lvl
    self.threads = []
    for tid in self.get_threads():
      self.threads.append(Thread(tid, lvl+1))


class Thread:
  def __init__(self, id, lvl):
    self.id = id
    self.lvl = lvl


# TODO: assert only one-node is supported
class OnlineCPUTopology:
  cpus = []
  cpus_no_ht = []
  ht_siblings = {}

  def get_thread_sibling(self, cpu):
    siblings = read_int_list(PREFIX + "cpu/cpu%s/topology/thread_siblings_list" % cpu)
    siblings.remove(cpu)
    assert len(siblings) == 1, "more than one sibling??"
    return siblings[0]

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


def filter_ht(cpus: list):
  virtuals = set()
  for cpu in cpus:
    siblings = read_int_list(PREFIX + "cpu/cpu%s/topology/thread_siblings_list" % cpu)
    assert len(siblings) == 1 or len(siblings) == 2, \
      "Hmm... Hyper-Threading with more than two siblings??"
    if len(siblings) == 2:
      virtuals.add(siblings[1])
  return list( filter(lambda c: c not in virtuals, cpus) )



if __name__ == '__main__':
  print(OnlineCPUTopology())
  # print(PC())