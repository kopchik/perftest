#!/usr/bin/env python3
# required: bridge_utils, qemu, lscgroup
from utils import run, retry, check_idleness, wait_idleness
from signal import signal, SIGINT, SIGCHLD, SIG_IGN
from collections import OrderedDict, namedtuple
from resource import setrlimit, RLIMIT_NOFILE
from useful.typecheck import type_check
from subprocess import Popen, PIPE
from traceback import format_tb
from pymongo import MongoClient
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
import os


info    = lambda *x: cprint(" ".join(map(str, x)), color='green')
warning = lambda *x: cprint(" ".join(map(str, x)), color='yellow')
error   = lambda *x: cprint(" ".join(map(str, x)), color='red')
die     = lambda m: sys.exit(m)
log     = Log("MASTER")
evsets = dict(
  basic   = "cycles instructions".split(),
  partial = "cycles instructions cache-references cache-misses branches branch-misses page-faults minor-faults major-faults LLC-loads LLC-load-misses LLC-stores".split(),
  full    = perftool.get_useful_events(),
)


class cfg:
  warmup  = 30
  measure = 180
  idfactor= 7
  vmstart = 10  # how much time a VM usually starts


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

def selectb(*names):
  return  {k:v for k,v in benchmarks.items() if k in names}

def perf_single(vm, col=None, cfg=cfg, benchmarks=benchmarks, events=['cycles']):
  assert col, "please provide DB collection to store results into"
  vmpid = vm.pid
  RPopen = vm.rpc.root.Popen
  for name, cmd in benchmarks.items():
    # start
    log.notice("launching %s (%s)" % (name, cmd))
    p = RPopen(cmd)  # p -- benchmark pipe
    log.notice("warmup sleeping for %s" % cfg.warmup)
    time.sleep(cfg.warmup)
    # measurement
    stat = perftool.stat(pid=vmpid, events=events, t=cfg.measure, ann=name, norm=True)
    col.save(stat)
    log.info(stat)
    # termination
    assert p.poll() is None, "test unexpectedly terminated"
    p.killall()
    wait_idleness(cfg.idfactor*2)


def myperf_single(vm, col=None, cfg=cfg, benchmarks=benchmarks):
  assert col, "please provide DB collection to store results into"
  vmpid = vm.pid
  RPopen = vm.rpc.root.Popen
  cg = vm.cg
  for name, cmd in benchmarks.items():
    # start
    log.notice("launching %s (%s)" % (name, cmd))
    p = RPopen(cmd)  # p -- benchmark pipe
    log.notice("warmup sleeping for %s" % cfg.warmup)
    time.sleep(cfg.warmup)

    # measurement
    cg.enable_ipc()
    cg.get_ipc(reset=True)
    log.notice("measuring for %s" % cfg.measure)
    time.sleep(cfg.measure)
    ipc = cg.get_ipc()
    stat = {"instructions", ipc}
    cg.disable_ipc()
    col.save(stat)
    log.info(stat)
    # termination
    assert p.poll() is None, "test unexpectedly terminated"
    p.killall()
    wait_idleness(cfg.idfactor*2)


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


class RPCMgr:
  def __init__(self, names):
    self.names = names

  def __enter__(self):
    vms = {}
    for n in self.names:
      vms[n] = cgmgr.start_vm(n)
    time.sleep(cfg.vmstart)
    for vm in vms.values():
      rpc = retry(rpyc.connect, args=(str(vm.addr),), kwargs={"port":6666}, retries=10)
      vm.rpc = rpc
    return vms

  def __exit__(self, t, v, tb):
    if t:
      log.critical("Got exception %s: %s" % (t,v))
      log.critical("\n".join(format_tb(tb)))
    cgmgr.graceful()


def main():
  parser = argparse.ArgumentParser(description='Run experiments')
  parser.add_argument('--debug', default=False, const=True, action='store_const', help='enable debug mode')
  parser.add_argument('-t', '--tests', default=['single', 'double', 'random', 'perf_single'], nargs='*')
  parser.add_argument('-e', '--events', default=perftool.get_useful_events(), nargs='*')
  parser.add_argument('--db', required=True, help="name of mongo database")
  parser.add_argument('--no-start', type=bool, default=False,
      help="Assume that instances are already started. Images are not regenerated, \
            VMs are not killed on start.")
  parser.add_argument('--idlness', type=bool, const=True, default=False, nargs='?',
      help="measure idlness and exit")

  args = parser.parse_args()

  # INIT
  if os.geteuid() != 0:
    sys.exit("you need root to run this scrips")
  setrlimit(RLIMIT_NOFILE, (10240, 10240))
  #signal(SIGCHLD, SIG_IGN)
  #signal(SIGINT,  SIG_IGN)
  topology = numa.OnlineCPUTopology()
  log.notice("topology:\n%s" % topology)
  cpu_name = numa.get_cpu_name()
  log.debug("cpu name: %s" % cpu_name)
  #events = perftool.get_useful_events()
  #log.debug("useful events: %s", events)
  mongo_client = MongoClient()
  db = mongo_client[args.db]

  # MACHINE-SPECIFIC CONFIGURATION
  hostname = socket.gethostname()
  if hostname == 'fx':
    run("hdparm -S 0 /dev/sda", sudo="root")
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
    log.critical("Warning! Debug enabled. Using debug database")
    log.notice(args)
    cfg.warmup   = 0.5
    cfg.measure  = 0.5
    cfg.idfactor*= 10
    db = mongo_client[args.db+'_debug']

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
    db.single.drop()
    col = db.single
    with RPCMgr("0") as vms:
      vm = vms["0"]
      wait_idleness(cfg.idfactor*2)
      r = perf_single(vm=vm, cfg=cfg, col=col, events=args.events)


  # EXPERIMENT 5: measurements stability
  if 'perf_stab' in args.tests:
    full_events = args.events
    vmname = str(cpus_far[0])
    with RPCMgr(vmname) as vms:
      vm = vms[vmname]
      log.notice("running tests on VM "+ vmname)
      wait_idleness(cfg.idfactor*2)
      for attempt in range(3):
        for name, evset in evsets.items():
          for t in [1, 3, 10, 30, 90, 180, 300]:
            cfg.measure = t if not args.debug else 1
            col = db["stab_%s_%ss"%(name,t)]
            r = myperf_single(vm=vm, cfg=cfg, col=col, benchmarks=benchmarks, events=evset)


if __name__ == '__main__':
  main()
