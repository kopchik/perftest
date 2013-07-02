#!/usr/bin/env python3
from socket import gethostname
from subprocess import *
import atexit
import shlex
import os


HOSTNAME = gethostname()
if HOSTNAME == "ux32vd":
  PREFIX = "/mnt/btrfs/"
elif HOSTNAME == "u2":
  PREFIX = "/home"
else:
  raise Exception("Unknown host. Please add configuration for it.")

def prepare():
  regen_cmd = "./imgregen.sh -n4 -t {prefix}/perftemplate -d {prefix}/perf" \
              .format(prefix=PREFIX)
  out = check_output(regen_cmd, shell=True)


def run(cmd, sudo=False):
  if isinstance(cmd, str):
    cmd = shlex.split(cmd)
  if sudo:
    cmd = ["sudo", "-u", sudo] + cmd
  check_call(cmd)

def run_(*args, **kwargs):
  try:
    run(*args, **kwargs)
  except Exception as err:
    print("ignoring:", err)

class LXC:
  def __init__(self, name, path, tpl):
    self.name = name
    self.path = path
    self.tpl = tpl
    self.started = False
    self.destroy()
    run("btrfs subvolume snapshot %s %s"%(tpl, path), sudo='root')
    run("lxc-create"
        " -t /home/exe/github/kvmtests/arm/configs/lxc-template.py -n %s"
        " -- --root %s " %(name, path), sudo='root')

  def start(self):
    if self.started:
      return
    run()

  def stop(self):
    run("lxc-shutdown -n %s"%self.name, sudo='root')

  def destroy(self):
    run_("lxc-destroy -n %s"%self.name, sudo='root')
    run_("btrfs subvolume delete %s"%self.path, sudo='root')


if __name__ == '__main__':
  # if os.getuid() != 0:
    # raise Exception("please run from root")
  # prepare()
  lxc = LXC(name="perf0", path="/mnt/btrfs/perf0/", tpl="/mnt/btrfs/perftemplate/")

