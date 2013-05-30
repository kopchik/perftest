#!/usr/bin/env python3

net = dict(
pgbench = "sudo -u postgres pgbench -c 20 -s 10 -T 100000",
nginx_static = "siege -c 100 -t 666h http://localhost/big_static_file",  # TODO: too CPU consuming,
wordpress = "siege -c 100 -t 666h http://localhost/",
)

single = dict(
  #matrix = "/home/sources/kvmtests/benches/matrix.py -s 1024 -r 1000",
  sdag   = "/home/sources/test_SDAG/test_sdag -t 5 -q 1000 /home/sources/test_SDAG/dataset.dat",
  sdagp  = "/home/sources/test_SDAG/test_sdag+ -t 5 -q 1000 /home/sources/test_SDAG/dataset.dat",
  blosc  = "/home/sources/kvmtests/benches/pyblosc.py",
  matrix = "/home/sources/kvmtests/benches/matrix 2048",
  ffmpeg = "ffmpeg -i /home/sources/avatar_trailer.m2ts \
            -threads 1 -t 10 -y -strict -2 -loglevel panic \
            -acodec aac -aq 100 \
            -vcodec libx264 -preset fast -crf 22 \
            -f mp4 /dev/null",
)

all = dict(single, **net)

if __name__ == '__main__':
  from pprint import pprint
  print("Single tests:")
  pprint(single)
  print("Network tests with two parts:")
  pprint(net)
  print("All tests together:")
  pprint(all)
