#!/usr/bin/env python3

from utils import run, retry, wait_idleness
from perftool import get_useful_events
from virt import cgmgr


benchmarks = dict(
matrix = "/home/sources/kvmtests/benches/matrix 2048",
integer = "/home/sources/kvmtests/benches/int",
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
blosc = "/home/sources/kvmtests/benches/pyblosc.py",
)


BOOT_TIME = 15
WARMUP_TIME = 30
MEASURE_TIME = 180
IDLENESS = 3

events = get_useful_events()
events = ",".join(r)

with cgmgr:
  vm = cgmgr.start("0")
  pid = vm.pid
  time.sleep(BOOT_TIME)
  rpc = retry(rpyc.connect, args=(str(vm.addr),), kwargs={"port":6666}, retries=10)
  RPopen = rpc.root.Popen
  #TODO: idleness
  for name, cmd in benchmarks.items():
    wait_idleness(IDLENESS*2.3)
    perf_cmd = "sudo kvm stat -e {events} -x, -p {pid} sleep {t} -o results/single/{out}" \
               .format(pid=pid, t=MEASURE_TIME, events=events, out=name)
    p = RPopen(cmd)
    time.sleep(WARMUP_TIME)
    run(perf_cmd)
    assert p.poll() is None, "test unexpectedly terminated"
    p.killall()