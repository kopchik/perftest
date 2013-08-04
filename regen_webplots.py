#!/usr/bin/env python3
from tests.benches import benches
from useful.mstring import s
from plotter import perfbars
import sys
import os

pids = []
def forkbg(f):
  def wrapper(*args, **kwargs):
    global pids
    pid = os.fork()
    if pid:
      pids += [pid]
      return
    f(*args, **kwargs)
    sys.exit("[%s] done" % os.getpid())
  return wrapper


@forkbg
def regen(datadir, outputdir, sibling=True, quiet=True):
  for bg in benches:
    for fg in benches:
      try:
        os.makedirs(s("${outputdir}/${bg}"))
      except FileExistsError:
        pass

      out = s("${outputdir}/${bg}/${fg}.png")
      single = s("${datadir}/single/${fg}")
      if sibling: double = s("${datadir}/double/${bg}/${fg}")
      else:       double = s("${datadir}/double_far/${bg}/${fg}")
      # print("perf bars params:", out, single, double)
      perfbars([single, double], output=out, quiet=True)

if __name__ == '__main__':
  print("u2")
  regen("results/u2/", "./static/u2/")
  print("fx far")
  regen("results/fx/", "./static/fx_far/", sibling=False)
  print("fx near")
  regen("results/fx/", "./static/fx_near/")
  #print("panda")
  #regen("results/panda/notp/", "./static/panda/")
  print("ux32vd")
  regen("results/ux32vd", "./static/ux32vd/")


  print("waiting workers to complete")
  for p in pids:
    try:
      os.waitpid(p, 0)
    except ChildProcessError:
      pass