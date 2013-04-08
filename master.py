#!/usr/bin/env python3
# required: bridge_utils, qemu, lscgroup
from collections import OrderedDict, namedtuple
from signal import SIGINT
from useful.typecheck import type_check
from utils import retry, check_idleness, wait_idleness
from subprocess import Popen, PIPE
from termcolor import cprint
from useful.log import Log
from virt import cgmgr
import subprocess
import argparse
import perftool
import socket
import random
import cgroup
import rpyc
import numa
import time
import sys
import pdb


info    = lambda *x: cprint(" ".join(map(str, x)), color='green')
warning = lambda *x: cprint(" ".join(map(str, x)), color='yellow')
error   = lambda *x: cprint(" ".join(map(str, x)), color='red')
die     = lambda m: sys.exit(m)
log     = Log("MASTER")

class cfg:
  warmup  = 15
  measure = 180
  idfactor= 7

benchmarks = dict(
matrix = "/home/sources/cputests/matrix.py 1024 1000",
pgbench = "sudo -u postgres pgbench -c 20 -s 10 -T 100000",
nginx_static = "siege -c 100 -t 666h http://localhost/big_static_file",  # TODO: too CPU consuming,
wordpress = "siege -c 100 -t 666h http://localhost/",
ffmpeg = "bencher.py -s 100 -- ffmpeg -i /home/sources/avatar_trailer.m2ts \
            -threads 1 -t 10 -y -strict -2 -loglevel panic \
            -acodec aac -aq 100 \
            -vcodec libx264 -preset fast -crf 22 \
            -f mp4 /dev/null",
sdag  = "bencher.py -s 100 -- /home/sources/test_SDAG/test_sdag -t 5 -q 1000 /home/sources/test_SDAG/dataset.dat",
sdagp = "bencher.py -s 100 -- /home/sources/test_SDAG/test_sdag+ -t 5 -q 1000 /home/sources/test_SDAG/dataset.dat",
blosc = "/home/sources/blosc_test.py",
)

classes = dict(
double = "classes/build/double",
int = "classes/build/int",
polute = "classes/build/polute"
)


def perf_single(vmpid, RPopen, benchmarks=benchmarks):
  result = {}
  for name, cmd in benchmarks.items():
    # start
    log.debug("launching %s (%s)" % (name, cmd))
    p = RPopen(cmd)  # p -- benchmark pipe

    # measurement
    log.debug("warmup sleeping")
    time.sleep(cfg.warmup)
    stat = perftool.stat(pid=vmpid, events=['cycles'], t=cfg.measure)
    result[name] = stat
    print(result)

    # termination
    assert p.poll() is None, "test unexpectedly terminated"
    p.killall()
    wait_idleness(cfg.idfactor*2)
  return result


def measure_single(cg, Popen, benchmarks=benchmarks):
  info("measuring performance of single tasks")
  global warmup
  global measure

  single_ipc = OrderedDict()
  for b in benchmarks:
    print("starting", b)
    p = Popen(benchmarks[b])
    time.sleep(warmup)  # warm-up
    cg.enable_ipc()
    cg.get_ipc(reset=True)

    #MEASUREMENT
    time.sleep(measure)
    ipc = cg.get_ipc()
    single_ipc[b] = ipc
    print(single_ipc)

    # TEST TERMINATION
    cg.disable_ipc()
    assert p.poll() is None, "test unexpectedly terminated"
    p.killall()
    # wait till the test is terminated completely
    wait_idleness(cfg.idfactor*2)
  print("the resulting IPC is:\n", single_ipc)
  return single_ipc


def measure_double(cg1, cg2, Popen1, Popen2, benchmarks=benchmarks):
  global warmup
  global measure
  assert cg1 and cg2, "I need cgroups to work with"

  info("measuring performance of TWO tasks")
  double_ipc = OrderedDict()

  for b1 in benchmarks:
    for b2 in benchmarks:
      wait_idleness()
      print("starting", b1, b2, end=' ')
      p1 = Popen1(benchmarks[b1])
      time.sleep(warmup)
      p2 = Popen2(benchmarks[b2])
      print(".")
      cg1.enable_ipc()
      # cg1.get_ipc(reset=True)
      cg2.enable_ipc()
      # cg2.get_ipc(reset=True)

      # MEASUREMENT
      time.sleep(measure)
      ipc1 = cg1.get_ipc()
      ipc2 = cg2.get_ipc()
      double_ipc[b1,b2] = (ipc1, ipc2)
      print(double_ipc)

      # TERMINATION
      assert p1.poll() is None, "test unexpectedly terminated on p1"
      assert p2.poll() is None, "test unexpectedly terminated on p2"
      p1.killall()
      p2.killall()
      cg1.disable_ipc()
      cg2.disable_ipc()
  warning("the resulting double ipc:\n", double_ipc)
  return double_ipc


def arbitrary_tests(instances=None, cpucfg=[1,1], num=10, benchmarks=benchmarks):
  vms = len(instances)
  result = []

  for x in range(num):
    pipes = []
    tstcfg = []
    wait_idleness()
    for i, cnt in enumerate(cpucfg):
      bs = []
      for _ in range(cnt):
        b = random.choice(list(benchmarks))
        bs.append(b)
        print("on cpu {} we start {}".format(i, b))
        Popen = instances[i].Popen
        pipes += [Popen(benchmarks[b])]
        time.sleep(warmup/vms*1.5)  # warm-up
      tstcfg += [bs]

    for inst in instances:
      inst.cg.enable_ipc()
    time.sleep(measure)
    ipcs = []
    for inst in instances:
      ipcs += [inst.cg.get_ipc()]
      inst.cg.disable_ipc()

    for p in pipes:
      assert p.poll() is None, "test unexpectedly terminated"
      p.killall()
    result.append((tstcfg, ipcs))
    print(result)
  return result




    # self.idfactor =  check_idleness(t=3)
    # self.log.notice("idfactor is %s" % self.idfactor)
    # assert self.idfactor <= 7, "is the machine really idle?"

  def start(self):
    cgroups = []
    rpcs = []
    self.stop()  # just to be sure

    #START KVMS
    info("starting kvms")
    for n in self.cpus:
      cgkvm = CGKVM(n)
      time.sleep(0.5)  # interval between launching

    # WAIT TILL THEY START UP
    idleness = self.idfactor*(len(self.cpus)+2)
    self.log.info("waiting for instances, expected idleness is <%s" % idleness)
    time.sleep(15)
    wait_idleness(idleness)

    # CREATE RPC CONNECTIONS
    info("making connections")
    for cpu in self.cpus:
      host = "172.16.5.%s" % (cpu+1)
      print("connecting to", host)
      rpcs += [rpyc.connect(host, port=6666)]

    for i, cg in enumerate(cgroups):
      instance = Instance(cg=cg, rpc=rpcs[i],
                          Popen=rpcs[i].root.Popen)




def main():
  parser = argparse.ArgumentParser(description='Run experiments')
  parser.add_argument('--debug', default=False, type=bool, const=True, nargs='?', help='enable debug mode')
  parser.add_argument('-t', '--tests', default=['single', 'double', 'random', 'perf_single'], nargs='*')
  parser.add_argument('--no-start', type=bool, default=False,
      help="Assume that instances are already started. Images are not regenerated, \
            VMs are not killed on start.")
  parser.add_argument('--idlness', type=bool, const=True, default=False, nargs='?',
      help="measure idlness and exit")

  args = parser.parse_args()

  # INIT
  topology = numa.OnlineCPUTopology()
  log.notice("topology:\n%s" % topology)
  cpu_name = numa.get_cpu_name()
  log.debug("cpu name: %s" % cpu_name)

  # MACHINE-SPECIFIC CONFIGURATION
  hostname = socket.gethostname()
  if hostname == 'fx':
    cpus_near = []
    cpu1 = topology.cpus[0]
    cpu2 = topology.ht_siblings[cpu1]
    cpus_near = [cpu1, cpu2]
    del cpu1, cpu2
    cpus_far = topology.cpus_no_ht[:2]
    cpus_all = topology.cpus
  elif hostname == 'ux32vd':
    cpus_near = topology.cpus_no_ht
    cpus_far = None
    cpus_all = topology.cpus_no_ht
    cfg.idfactor = 3
  elif hostname == 'p1':
    cpus_near = topology.cpus_no_ht
    cpus_far = None
    cpus_all = cpus_near
  else:
    raise Exception("No profile for machine % " % hostname)
  print("cpus_near:", cpus_near, "cpus_far:", cpus_far)

  if args.debug:
    log.critical("Warning! Debug enabled")
    log.notice(args)
    cfg.warmup  /= 10
    cfg.measure /= 30
    cfg.idfactor *= 100

  # PRE-FLIGHT CHECK
  if not args.no_start:
    warning("killing all kvms")
    cgmgr.graceful(timeout=30)
    subprocess.call("/home/sources/perftests/regen_img.sh")
    subprocess.check_output("sync")

  if args.idlness:
    log.debug("measuring idlness")
    return print("idleness is", check_idleness())

  # EXPERIMENT 1: SINGLE TASK PERFORMANCE (IDEAL PERFORMANCE)
  if 'single' in args.tests:
    instances = start_instances([cpus_near[0]])
    inst = instances[0]
    measure_single(cg=inst.cg, Popen=inst.Popen)
    stop_instances(instances)

  # EXPERIMENT 2: TWO TASK PERFORMANCE
  # near
  if 'double' in args.tests:
    instances = start_instances(cpus_near)
    inst1 = instances[0]
    inst2 = instances[1]
    measure_double(cg1=inst1.cg, cg2=inst2.cg, Popen1=inst1.Popen, Popen2=inst2.Popen)
    stop_instances(instances)
    # far
    if cpus_far:
      instances = start_instances(cpus_far)
      inst1 = instances[0]
      inst2 = instances[1]
      measure_double(cg1=inst1.cg, cg2=inst2.cg, Popen1=inst1.Popen, Popen2=inst2.Popen)
      stop_instances(instances)

  # EXPERIMENT 3: arbitrary tests
  if 'random' in args.tests:
    with VMS(cpus_all) as instances:
      arbitrary_tests(instances=instances, cpucfg=[1 for _ in cpus_all], num=1000)

  # EXPERIMENT 4: test with all counters enabled
  if 'perf_single' in args.tests:
    with cgmgr:
      vmpid = cgmgr.start("0")
      time.sleep(10)
      # TODO wait_idleness(7)
      rpc = retry(rpyc.connect, args=("172.16.5.10",), kwargs={"port":6666}, retries=10)
      RPopen = rpc.root.Popen
      perf_single(vmpid=vmpid, RPopen=RPopen)


if __name__ == '__main__':
  main()