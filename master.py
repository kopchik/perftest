#!/usr/bin/env python3
from collections import OrderedDict, namedtuple
from useful.typecheck import type_check
from useful.log import Log
from termcolor import cprint
import subprocess
import argparse
import socket
import random
import cgroup
import rpyc
import numa
import time
import sys
# required: brdge_utils, qemu, lscgroup

info    = lambda *x: cprint(" ".join(map(str, x)), color='green')
warning = lambda *x: cprint(" ".join(map(str, x)), color='yellow')
error   = lambda *x: cprint(" ".join(map(str, x)), color='red')
die     = lambda m: sys.exit(m)

warmup   = 15
measure  = 180
idfactor = 1
maxbusy  = 1

class CG(cgroup.PerfEvent, cgroup.CPUSet):
  pass
Instance = namedtuple("Instance", ["cg", "kvmp", "rpc", "Popen"])

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


container = "systemd-nspawn -D /home/arch64_perf/ /home/sources/slave.py {port}"
kvm_cmd = """
qemu-system-x86_64 --enable-kvm
-smp 1 -m 1G -drive
file=/home/sources/perftests/arch64_perf{n}.qcow2,if=virtio,cache=unsafe
 -net nic,model=e1000,macaddr=52:54:91:5E:38:0{n}
 -net tap,ifname=tap{n},script=kvm-ifup.sh,downscript=no
 -vnc localhost:{n}
"""
counters_cmd = """perf list hw sw cache tracepoint | awk '{print $1}' |  grep -v '^$' | tr '\n' ','"""


def check_idleness(t=10, thr=0.1):
  cmd = "sudo perf stat -a -e cycles --log-fd 1 -x, sleep {t}"
  cycles_raw = subprocess.check_output(cmd.format(t=t), shell=True)
  cycles = int(cycles_raw.decode().split(',')[0])
  return (cycles / t) / 10**7


def wait_idleness():
  warned = False
  time.sleep(0.3)
  while True:
    busy = check_idleness(t=3)
    if busy < maxbusy:
      break
    if not warned:
      warning("node is still busy more than", maxbusy)
      warned = True
    print(busy, end=' ')
    sys.stdout.flush()
    time.sleep(1)


def perf_single(cg=None, Popen=None, benchmarks=benchmarks):
  perf_single = OrderedDict()
  p = Popen(counters_cmd, stdout=subprocess.PIPE)
  print(p.stdout.readall())
  die("basta cosi")
  for n,b in benchmarks.items():
    # start
    print("starting", n)
    p = Popen(b)
    time.sleep(warmup)
    cg.enable_ipc()
    cg.get_ipc(reset=True)

    # measurement
    time.sleep(measure)
    perf_single[n] = cg.get_ipc()
    print("IPC", perf_single[n])

    # termination
    assert p.poll() is None, "test unexpectedly terminated"
    p.killall()
    wait_idleness()
  return perf_single


# @type_check
def measure_single(cg: CG=None, Popen=None, benchmarks=benchmarks):
  info("measuring performance of single tasks")
  assert cg and Popen and benchmarks, "please provide cg, Popen and benchmarks"
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
    wait_idleness()
  print("the resulting IPC is:\n", single_ipc)
  return single_ipc


# @type_check
def measure_double(cg1: CG=None, cg2: CG=None, Popen1=None, Popen2=None, benchmarks=benchmarks):
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


def start_instances(cpus=[]):
  assert cpus, "please provide cpus"
  cgroups = []
  kvmpipes = []
  rpcs = []
  result = []

  #START KVMS
  info("starting kvms")
  for n in cpus:
    cg = CG(path="/cg%s" % n, cpus=[n])
    cgroups  += [cg]
    cmd = kvm_cmd.format(n=n)
    print("starting", cmd)
    kvmpipes += [cg.exec(cmd, bg=True)]
    time.sleep(1)  # interval between launching


  # WHAIT TILL THEY START UP
  info("waiting till they finish init")
  time.sleep(15)
  wait_idleness()

  # CREATE RPC CONNECTIONS
  info("making connections")
  for cpu in cpus:
    host = "172.16.5.%s" % (cpu+1)
    print("connecting to", host)
    rpcs += [rpyc.connect(host, port=6666)]

  for i, cg in enumerate(cgroups):
    instance = Instance(cg=cg, kvmp=kvmpipes[i], rpc=rpcs[i], Popen=rpcs[i].root.Popen)
    result.append(instance)
  return result


def stop_instances(instances):
  info("sending powerdown commands")
  for instance in instances:
    instance.Popen('poweroff')
    instance.rpc.close()

  #WAIT FOR SHUTDOWN
  for instance in instances:
    print("waiting for", instance.kvmp, "container")
    instance.kvmp.wait()
    instance.cg.killall()
    instance.cg.leave_subsys()


class open_vms:
  def __init__(self, cpus=[]):
    self.log = Log("VMS")
    self.cpus = cpus

  def __enter__(self):
    self.log.info("starting instances")
    self.instances = start_instances(self.cpus)
    return self.instances

  def __exit__(self, type, value, traceback):
    self.log.info("terminating instances")
    stop_instances(self.instances)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Run experiments')
  parser.add_argument('--debug', default=False, type=bool, const=True, nargs='?', help='enable debug mode')
  parser.add_argument('-t', '--tests', default=['single', 'double', 'random', 'perf_single'], nargs='*')
  parser.add_argument('--no-start', type=bool, default=False,
      help="Assume that instances are already started. Images are not regenerated, \
            VMs are not killed on start.")

  args = parser.parse_args()
  print(args)


  # INIT
  if args.debug:
    error("Warning! Debug enabled")
    warmup /= 10
    measure /= 30
    idfactor *= 100
  topology = numa.OnlineCPUTopology()
  #TODO: dump topology
  cpu_name = numa.get_cpu_name()
  hostname = socket.gethostname()

  # MACHINE-SPECIFIC CONFIGURATION
  if cpu_name.find("AMD") != -1:
    global idfactor
    idfactor = 3
    cpus_near = []
    cpu1 = topology.cpus[0]
    cpu2 = topology.ht_siblings[cpu1]
    cpus_near = [cpu1, cpu2]
    del cpu1, cpu2
    cpus_far = topology.cpus_no_ht[:2]
    cpus_all = topology.cpus
  elif cpu_name.find("Intel") != -1:
    if hostname == 'ux32vd':
      cpus_near = topology.cpus_no_ht
      cpus_far = None
      cpus_all = topology.cpus_no_ht
    else:
      raise Exception("Unknown configuration")
  else:
    raise Exception("Unknown machine")
  print("cpus_near:", cpus_near, "cpus_far:", cpus_far)


  # PRE-FLIGHT CHECK
  if not args.no_start:
    warning("killing all kvms")
    subprocess.call("killall -w -q kvm".split())
    subprocess.call("/home/sources/perftests/regen_img.sh")
    subprocess.check_output("sync")

  # EXPERIMENT 1: SINGLE TASK PERFORMANCE (IDEAL PERFORMANCE)
  if 'single' in args.tests:
    maxbusy = idfactor
    instances = start_instances([cpus_near[0]])
    inst = instances[0]
    measure_single(cg=inst.cg, Popen=inst.Popen)
    stop_instances(instances)

  # EXPERIMENT 2: TWO TASK PERFORMANCE
  # near
  if 'double' in args.tests:
    maxbusy = idfactor*2
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
    maxbusy = idfactor * len(cpus_all)
    instances = start_instances(cpus_all)
    arbitrary_tests(instances=instances, cpucfg=[1 for _ in cpus_all], num=1000)
    stop_instances(instances)

  # EXPERIMENT 4: test with all counters enabled
  if 'perf_single' in args.tests:
    with open_vms([cpus_near[0]]) as instances:
      inst = instances[0]
      perf_single(cg=inst.cg, Popen=inst.Popen)