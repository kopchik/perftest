#!/usr/bin/env python3
from operator import mul
from functools import reduce
from itertools import product
from math import sqrt
from collections import OrderedDict
from termcolor import colored, cprint

# u2
interference = OrderedDict([
#~           & blosc &ffmpeg &integer &matrix &nginx &pgbench &sdag &sdagp &wordpress \\
 ("blosc",     [0.9,  4.7,  0.3, 13.3,  8.7, 11.4, 10.7,  9.8,  6.9,])
,("ffmpeg",    [1.1,  2.3,  0.2,  9.2,  2.8,  8.3,  4.3,  7.4,  3.1,])
,("intege",    [-0.7, 0.01, -0.1, -0.1, -1.8, -0.8,  0.1,  0.7, -0.6,])
,("matrix",    [9.6,  8.4,  0.3, 15.4, 21.9, 24.7, 22.8, 41.3, 14.0,])
,("nginx",     [3.4,  7.5,  0.5, 18.0,  8.4, 15.2, 14.4, 16.2, 10.5,])
,("pgbenc",    [5.2,  6.5,  0.4, 16.8, 19.4,  8.3, 12.4, 12.6, 10.9,])
,("sdag",      [0.1,  2.6,  0.2,  8.5,  4.9, 10.8,  5.3,  9.0,  3.7,])
,("sdagp",     [4.2, 10.0,  0.3, 15.4, 20.1, 27.8, 24.0, 50.3, 14.8,])
,("wp",        [3.1,  4.8,  0.2,  9.8,  9.3, 15.5, 11.1, 12.9,  6.8,])
])

mean  = lambda l: sum(l)/len(l)
gmean = lambda l: pow(reduce(mul, l),1/len(l))

def err(l1, l2):
  return sum(abs(1-v1/v2) for v1, v2 in zip(l1,l2))/len(l1)

def pivot(tbl):
  tbl2 = OrderedDict()
  for b in tbl:
    tbl2[b]=[]
  for i, column in enumerate(tbl):
    for row in tbl:
        tbl2[column].append( tbl[row][i] )
  return tbl2


def printbl(tbl):
  errtbl = error(tbl)
  tpl = "{:>7}"
  tplf = "{:>7.0%}"
  n = int(sqrt(len(tbl)))
  print(tpl.format(" "), end=" ")
  [print(tpl.format(k), end="") for k in tbl]; print()
  for t1 in tbl:
    print(tpl.format(t1), end=" ")
    errs = 0.0
    for t2 in tbl:
      v = errtbl[t1,t2]
      errs += v
      if v > 3:
        v = ">"
        #print("{:>6}".format("-"), end=" ")
        cprint(tpl.format(" "), end="")
      else:
        color = "white"
        if   v < 1: color = "green"
        elif v < 2: color = "yellow"
        # else:       color = "white"
        cprint(tplf.format(v), color, end="")
    print(" ", "sum={:>5.0%}".format(errs))
  print()


def error(tbl):
  errtbl = {}
  for t1, t2 in product(tbl,tbl):
    errtbl[t1,t2] = err(tbl[t1], tbl[t2])
  return errtbl

sensitivity = pivot(interference)
cprint("INTERFERENCE", "green")
printbl(interference)
cprint("SENSITIVITY", "green")
printbl(sensitivity)