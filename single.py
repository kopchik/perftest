#!/usr/bin/env python3

from utils import run, retry, wait_idleness
from logging import basicConfig, getLogger, DEBUG
from resource import setrlimit, RLIMIT_NOFILE
from perftool import get_useful_events
from os.path import isdir
from os import geteuid
from virt import cgmgr
import argparse
import rpyc
import time
import gc


benchmarks = dict(
matrix = "bencher.py -s 100 -- /home/sources/kvmtests/benches/matrix 2048",
integer = "bencher.py -s 100 -- /home/sources/kvmtests/benches/int",
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
blosc = "/home/sources/kvmtests/benches/pyblosc.py -r 100000",
)


BOOT_TIME = 15
WARMUP_TIME = 30
MEASURE_TIME = 180
IDLENESS = 3

events = get_useful_events()
events = ",".join(events)

PERF_CMD = "sudo perf kvm stat -e {events} -x, -p {pid} -o {output} sleep {t}"


def main():
  log = getLogger(__name__)
  parser = argparse.ArgumentParser(description='Experiments with single tasks')
  parser.add_argument('--debug', default=False, const=True, action='store_const', help='enable debug mode')
  parser.add_argument('--prefix', required=True, help="prefix where to save the results")
  args = parser.parse_args()

  log.info(args)
  if geteuid() != 0:
    sys.exit("you need root to run this scrips")
  setrlimit(RLIMIT_NOFILE, (10240, 10240))
  if args.debug:
    basicConfig(level=DEBUG)
  assert isdir(args.prefix), "prefix should be a valid directory"

  gc.disable()
  with cgmgr:
    vm = cgmgr.start("0")
    time.sleep(BOOT_TIME)
    rpc = retry(rpyc.connect, args=(str(vm.addr),), kwargs={"port":6666}, retries=10)
    RPopen = rpc.root.Popen
    remains = len(benchmarks)
    for name, cmd in benchmarks.items():
      output = args.prefix + '/' + name
      perf_cmd = PERF_CMD.format(pid=vm.pid, t=MEASURE_TIME, events=events, output=output)

      log.debug("waiting for idleness")
      wait_idleness(IDLENESS*2.3)
      log.debug("starting %s" % name)
      p = RPopen(cmd)
      log.debug("warming up for %s" % WARMUP_TIME)
      time.sleep(WARMUP_TIME)
      log.debug("starting measurements")
      run(perf_cmd)
      assert p.poll() is None, "test unexpectedly terminated"
      log.debug("finishing tests")
      p.killall()
      gc.collect()


if __name__ == '__main__':
  main()