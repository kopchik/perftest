VERSION = (2, 10)
def min_version(v):
  assert v <= VERSION, "expected: %s, current: %s" % (v, VERSION)

from useful import __version__ as useful_version
assert useful_version >= (1,13), "too old useful version"
