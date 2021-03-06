#!/usr/bin/env python3

from logging import basicConfig, getLogger, DEBUG
from os.path import isdir, exists
from os import makedirs
import argparse
import time
import gc

from useful.mstring import s
from utils import run, retry, wait_idleness

from config import WARMUP_TIME, MEASURE_TIME, IDLENESS, BOOT_TIME
from config import VMS
from config import basis

log = getLogger(__name__)


def main():
  parser = argparse.ArgumentParser(description='Experiments with single tasks')
  parser.add_argument('--debug', default=False, const=True, action='store_const', help='enable debug mode')
  parser.add_argument('--prefix', required=True, help="prefix where to save the results")
  parser.add_argument('-t', '--tests', default=['single', 'double'], nargs='*')
  args = parser.parse_args()

  basicConfig(level=DEBUG)
  log.info(args)
  assert isdir(args.prefix), "prefix should be a valid directory"

  gc.disable()
  vm = VMS[0]
  vm.start()
  time.sleep(BOOT_TIME)

  if 'single' in args.tests:
    single(vm, args.prefix)
  if 'double' in args.tests:
    double(args.prefix)


def single(vm, prefix):
  outdir = s("${prefix}/single/")
  if not exists(outdir):
    makedirs(outdir)

  remains = len(basis)
  for name, cmd in basis.items():
    log.debug("remains %s tests" % remains)
    remains -= 1
    outfile = s("${prefix}/single/${name}")

    log.debug("waiting for idleness")
    wait_idleness(IDLENESS*2.3)
    log.debug("starting %s" % name)
    p = vm.Popen(cmd)
    log.debug("warming up for %s" % WARMUP_TIME)
    time.sleep(WARMUP_TIME)
    log.debug("starting measurements")
    vm.stat(outfile)
    assert p.poll() is None, "test unexpectedly terminated"
    log.debug("finishing test")
    p.killall()
    gc.collect()


def double(prefix, far=True):
  topology = CPUTopology()
  if far:
    cpu, bgcpu = topology.cpus_no_ht[:2]
  else:
    cpu = topology.cpus_no_ht[0]
    bgcpu = topology.ht_siblings[cpu][0]

  with cgmgr:
    vm = cgmgr.start(str(cpu))
    bgvm = cgmgr.start(str(bgcpu))
    time.sleep(BOOT_TIME)

    rpc = retry(rpyc.connect, args=(str(vm.addr),), kwargs={"port":6666}, retries=10)
    bgrpc = retry(rpyc.connect, args=(str(bgvm.addr),), kwargs={"port":6666}, retries=10)

    RPopen = rpc.root.Popen
    BGRPopen = bgrpc.root.Popen

    remains = len(benchmarks)**2

    for bgname, bgcmd in benchmarks.items():
      log.debug("waiting for idleness")
      wait_idleness(IDLENESS*3.3)
      log.warning("launching %s in bg" % bgname)
      bg = BGRPopen(bgcmd)
      log.debug("warming up for %s" % WARMUP_TIME)
      time.sleep(WARMUP_TIME)

      for name, cmd in benchmarks.items():
        print("remains %s tests" % remains)
        remains -= 1

        outdir = s("${prefix}/double/${bgname}/")
        try: os.makedirs(outdir)
        except FileExistsError: pass

        output =  outdir + name
        perf_cmd = PERF_CMD.format(pid=vm.pid, t=MEASURE_TIME, events=events, output=output)
        log.debug("starting %s" % name)
        p = RPopen(cmd)
        log.debug("warming up for %s" % WARMUP_TIME)
        time.sleep(WARMUP_TIME)
        log.debug("starting measurements")
        run(perf_cmd)
        assert p.poll() is None, "test unexpectedly terminated"
        assert bg.poll() is None, "bg process suddenly died :("
        log.debug("finishing tests")
        p.killall()
        gc.collect()
      bg.killall()
      time.sleep(1)


if __name__ == '__main__':
  main()
