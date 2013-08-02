#!/usr/bin/env python3
from pylab import *
from scipy.stats import norm
import sys

def average(a):
  return sum(a)/len(a)

# from http://matplotlib.org/examples/pylab_examples/histogram_percent_demo.html
@FuncFormatter
def to_percent(y, position):
  # Ignore the passed in position. This has the effect of scaling the default
  # tick locations.
  s = str(100 * y)

  # The percent symbol needs escaping in latex
  if matplotlib.rcParams['text.usetex'] == True:
    return s + r'$\%$'
  else:
    return s + '%'


COLOR = "#548BE3"
def main(argv):
  paths = argv[1:]
  if not paths:
    sys.exit("please specify files to plot")
  pltnum = len(argv)//2 + len(argv)%2
  for i, fname in enumerate(paths):
    with open(fname) as fd:
      values = []
      t = fd.readline().strip("#")
      for l in fd.readlines():
        values += [float(l.strip())]
      subplot(pltnum, 2, i+1)
      title(t)
      avg = average(values)
      percents = map(lambda x: avg/x-1, values)
      n, bins, patches = hist(list(percents),
        bins=50, normed=True,
        histtype='bar', color=COLOR)

      mu, sigma = norm.fit(values)
      y = normpdf(bins, mu, sigma)
      plot(bins,y, 'r-', linewidth=3)
      #print("bins:", bins)
      #print("y:", y)

    ## remove y axis
    yaxis = gca().yaxis
    # yaxis.set_visible(False)
    
    ## xaxis
    xaxis = gca().xaxis
    xaxis.set_major_formatter(to_percent)
    xaxis.set_major_locator(MaxNLocator(nbins=5, prune='lower'))

  tight_layout(pad=0.5)
  savefig("/home/exe/github/perf2013paper/pic/stab_test.eps")
  show()


if __name__ == '__main__':
  main(sys.argv)
