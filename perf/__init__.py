VERSION = (2, 5)
def min_version(v):
  assert v <= VERSION, "expected: %s, current: %s" % (v, VERSION)
