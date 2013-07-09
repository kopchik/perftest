from socket import gethostname

# LXC
HOSTNAME = gethostname()
if HOSTNAME == "ux32vd":
  LXC_PREFIX = "/mnt/btrfs/"
elif HOSTNAME in ["odroid", "u2"]:
  LXC_PREFIX = "/home/"
else:
  raise Exception("Unknown host. Please add configuration for it.")

WARMUP_TIME = 30
IDLENESS = 30
MEASURE_TIME = 180
TEARDOWN_TIME = 20
