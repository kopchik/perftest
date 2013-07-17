from config import *

benches = dict(
matrix  = "bencher.py -s 100000 -- /home/sources/perftest/benches/matrix 2048",
integer = "bencher.py -s 100000 -- /home/sources/perftest/benches/int",
pgbench = "sudo -u postgres pgbench -c 20 -s 10 -T 100000",
nginx   = "siege -q -c 100 -t 666h http://localhost/big_static_file",  # TODO: too CPU consuming,
wordpress = "siege -q -c 8 -t 666h http://localhost/",
ffmpeg  = "bencher.py -s 100000 -- ffmpeg -i /home/sources/avatar_10s.m2ts \
            -threads 1 -t 10 -y -strict -2 -loglevel panic \
            -acodec aac -aq 100 \
            -vcodec libx264 -preset fast -crf 22 \
            -f mp4 /dev/null",
sdag    = "bencher.py -s 100000 -- /home/sources/test_SDAG/test_sdag -t 5 -q 1000 /home/sources/test_SDAG/dataset.dat",
sdagp   = "bencher.py -s 100000 -- /home/sources/test_SDAG/test_sdag+ -t 5 -q 1000 /home/sources/test_SDAG/dataset.dat",
blosc   = "/home/sources/perftest/benches/pyblosc.py -r 100000",
)
