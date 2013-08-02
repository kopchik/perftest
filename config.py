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
config = Struct(
  hostname = "fx",
  virtualization = "qemu",
  has_siblings = True,
  results_path = "./results/fx/cc_auto/notp/"
  )
configs["fx"] = config