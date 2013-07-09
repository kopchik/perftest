#!/usr/bin/env python3
from os.path import exists, dirname
from ipaddress import IPv4Address
from socket import gethostname
from useful.log import Log
from os import makedirs

from lib.utils import wait_idleness
from lib.perftool import cgstat, get_useful_events
from lib.lxc import LXC

from tests.benches import benches
from config import *

import argparse
import rpyc
import time
import gc


log = Log("lxc")
log.set_verbosity("debug")


def main():
  parser = argparse.ArgumentParser(description='Run experiments')
  parser.add_argument('--debug', default=False, const=True, action='store_const', help='enable debug mode')
  args = parser.parse_args()
  print(args)
  if args.debug:
    global WARMUP_TIME, MEASURE_TIME, IDLENESS, TEARDOWN_TIME
    log.critical("debug mode enabled")
    WARMUP_TIME = 0
    MEASURE_TIME = 0.5
    IDLENESS = 70

  lxcs = []
  for x in range(4):
    ip = str(IPv4Address("172.16.5.10")+x)
    print(ip)
    name = "perf%s" % x
    lxc = LXC(name=name, root=LXC_PREFIX+name, tpl=LXC_PREFIX+"/perftemplate/",
              addr=ip, gw="172.16.5.1", cpus=[x])
    lxcs += [lxc]
    lxc.destroy()
    #lxc.create()
    # lxc.start()


  # single
  lxc = lxcs[0]
  lxc.create()
  lxc.start()
  log.debug("giving VMS time to start")
  events = get_useful_events()
  time.sleep(6)
  rpc = rpyc.connect(lxc.addr, port=6666)
  RPopen = rpc.root.Popen
  def stat(output):
    cgstat(path="lxc/"+lxc.name, events=events, t=MEASURE_TIME, out=output)
  single(RPopen, outdir="/home/sources/perftest/results/u2/single", stat=stat)

  # double
  bglxc = lxcs[1]
  bglxc.create()
  bglxc.start()
  time.sleep(6)
  bgrpc = rpyc.connect(lxc.addr, port=6666)
  BGPopen = bgrpc.root.Popen
  def stat(output):
    cgstat(path="lxc/"+lxc.name, events=events, t=MEASURE_TIME, out=output)
  double(RPopen, BGPopen, outdir="/home/sources/perftest/results/u2/double", stat=stat)


def single(Popen, outdir, stat, benches=benches):
  remains = len(benches)
  for name, cmd in benches.items():
    print("remains %s tests" % remains)
    remains -= 1
    output = outdir + '/' + name
    # prepare
    log.debug("waiting for idleness")
    wait_idleness(IDLENESS)
    log.debug("starting %s" % name)
    # warmup
    p = Popen(cmd)
    log.debug("warming up for %s" % WARMUP_TIME)
    time.sleep(WARMUP_TIME)
    # measurement
    log.debug("starting measurements")
    stat(outdir+'/'+name)
    # teardown
    assert p.poll() is None, "test unexpectedly terminated"
    log.debug("finishing tests")
    p.killall()
    gc.collect()


def double(Popen, BGPopen, outdir, stat, benches=benches):
  remains = len(benches)**2
  for bgname, bgcmd in benches.items():
    for name, cmd in benches.items():
        wait_idleness(IDLENESS)
        bgp = BGPopen(bgcmd)
        log.debug("warming up for %s" % WARMUP_TIME)
        time.sleep(WARMUP_TIME)

        log.debug("remains %s tests" % remains)
        remains -= 1
        output = "%s/%s/%s" % (outdir, bgname, name)
        if not exists(dirname(output)):
            makedirs(dirname(output))
        # start
        p = Popen(cmd)
        log.debug("warming up for %s" % WARMUP_TIME)
        time.sleep(WARMUP_TIME)
        # measurement
        log.debug("starting measurements")
        stat(output)
        # teardown
        assert p.poll() is None, "test unexpectedly terminated"
        log.debug("finishing tests")
        p.killall()
        log.debug("waiting %s for tear down" % TEARDOWN_TIME)
        time.sleep(TEARDOWN_TIME)

        assert bgp.poll() is None, "background task suddenly died"
        bgp.killall()
        gc.collect()
