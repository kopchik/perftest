#!/usr/bin/env python3
from setuptools import setup, find_packages
from perf import VERSION
setup(
  name = "perf",
  version = ".".join(map(str,VERSION)),
  packages = ['perf'],
)
