#!/usr/bin/env python3
from os import geteuid
import sys
import gc

if geteuid() != 0:
  sys.exit("you need root to run this scrips")

if len(sys.argv) < 2:
  sys.exit("please specify test name")

gc.disable()

testName = sys.argv.pop(1)
module = __import__("tests."+testName)
module = getattr(module, testName)
module.main()
