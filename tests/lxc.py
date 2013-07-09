#!/usr/bin/env python3
from ipaddress import IPv4Address
from socket import gethostname
from useful.log import Log

from lib.utils import wait_idleness
from lib.perftool import cgstat
from lib.lxc import LXC

from tests.benches import benches
from config import *

import rpyc
import time


log = Log("lxc")


def main():
  lxcs = []
  for x in range(4):
    ip = str(IPv4Address("172.16.5.10")+x)
    print(ip)
    name = "perf%s" % x
    lxc = LXC(name=name, root=LXC_PREFIX+name, tpl=LXC_PREFIX+"/perftemplate/",
              addr=ip, gw="172.16.5.1", cpus=[x])
    lxcs += [lxc]
    lxc.destroy()
    lxc.create()
    # lxc.start()


  # single
  lxc = lxcs[0]
  lxc.start()
  def stat(output):
    cgstat(path="lxc/"+lxc.name, events=['cycles'], t=1, out=output) #TODO:
  time.sleep(2)
  rpc = rpyc.connect(lxc.addr, port=6666)
  RPopen = rpc.root.Popen
  single(RPopen, outdir="./results/", stat=stat)


def single(Popen, outdir, stat, benches=benches):
  remains = len(benches)
  for name, cmd in benches.items():
    print("remains %s tests" % remains)
    remains -= 1
    output = outdir + '/' + name
    # prepare
    log.debug("waiting for idleness")
    wait_idleness(IDLENESS*2.3)
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