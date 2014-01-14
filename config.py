from socket import gethostname
from useful.mystruct import Struct

# LXC
HOSTNAME = gethostname()
if HOSTNAME == "ux32vd":
  LXC_PREFIX = "/mnt/btrfs/"
elif HOSTNAME in ["odroid", "u2"]:
  LXC_PREFIX = "/home/"
elif HOSTNAME == 'p1':
  LXC_PREFIX = "/mnt/btrfs/"
else:
  raise Exception("Unknown host. Please add configuration for it.")


WARMUP_TIME = 15
IDLENESS = 45
MEASURE_TIME = 180

configs = {}
# FX
configs["fx"] = Struct(
  name = "fx",
  virt = "qemu",
  siblings = True,
  results_path = "./results/fx/cc_auto/notp/"
  )

# U2
configs["odroid"] = Struct(
  name = "u2",
  virt = "lxc",
  siblings = False,
  results_path = "./results/fx/u2/"
  )


basis = dict(
  pgbench = "sudo -u postgres pgbench -c 20 -s 10 -T 100000",
  nginx_static = "siege -c 100 -t 666h http://localhost/big_static_file",  # TODO: too CPU consuming,
  wordpress = "siege -c 100 -t 666h http://localhost/",
  # matrix = "/home/sources/kvmtests/benches/matrix.py -s 1024 -r 1000",
  matrix = "/home/sources/kvmtests/benches/matrix 2048",
  sdag   = "/home/sources/test_SDAG/test_sdag -t 5 -q 1000 /home/sources/test_SDAG/dataset.dat",
  sdagp  = "/home/sources/test_SDAG/test_sdag+ -t 5 -q 1000 /home/sources/test_SDAG/dataset.dat",
  blosc  = "/home/sources/kvmtests/benches/pyblosc.py",
  ffmpeg = "ffmpeg -i /home/sources/avatar_trailer.m2ts \
            -threads 1 -t 10 -y -strict -2 -loglevel panic \
            -acodec aac -aq 100 \
            -vcodec libx264 -preset fast -crf 22 \
            -f mp4 /dev/null",
)


validate = dict(
  bitrix = "siege -c 100 -t 666h http://localhost/",
)