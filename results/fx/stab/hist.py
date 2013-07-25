#!/usr/bin/env python3
from pylab import *
from scipy.stats import norm
import sys

COLOR = "#548BE3"
def main(argv):
  argv.pop(0)
  if not argv:
    sys.exit("please provide the path to file")
  pltnum = len(argv)//2 + len(argv)%2
  for i, fname in enumerate(argv):
    with open(fname) as fd:
      values = []
      t = fd.readline().strip("#")
      for l in fd.readlines():
        values += [float(l.strip())]
      subplot(pltnum,2, i+1)
      title(t)
      n, bins, patches = hist(values, bins=50, normed=True,
        histtype='bar', color=COLOR)

      mu, sigma = norm.fit(values)
      y = normpdf(bins, mu, sigma)
      plot(bins,y, 'r-', linewidth=3)
      #print("bins:", bins)
      #print("y:", y)
    ## remove y axis
    yaxis = gca().yaxis
    # yaxis.set_visible(False)


  xaxis = gca().xaxis
  # xaxis.set_major_formatter(to_percent)
  xaxis.set_major_locator(MaxNLocator(nbins=5, prune='lower'))

  tight_layout(pad=0.5)
  savefig("/home/exe/github/perf2013paper/pic/stab_test.eps")
  show()


if __name__ == '__main__':
  main(sys.argv)
