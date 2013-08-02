#!/usr/bin/env python3
from tests.benches import benches
from useful.mstring import s
from plotter import perfbars
import os

def regen(datadir, outputdir, sibling=True):
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
      print(out, single, double)
      perfbars([single, double], output=out)

if __name__ == '__main__':
  print("u2")
  regen("results/u2/", "./static/u2/")
  # print("fx far")
  # regen("results/fx/cc_auto/notp/", "./static/fx_far/", sibling=False)
  # print("fx near")
  # regen("results/fx/cc_auto/notp/", "./static/fx_near/")
  # print("panda")
  # regen("results/panda/notp/", "./static/panda/")