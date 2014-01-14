#!/usr/bin/env python3
from operator import mul
from functools import reduce

#mean = lambda l: map(mul,l)/len(l)
mean = lambda l: pow(reduce(mul,l), 1/len(l))

def report(l):
  for v in l:
    print("{:.2f}".format(v), end=" ")
  print()

Rd = [417,83,66,39449, 772]
Md = [244,70, 153, 33527, 368]
Zd = [134, 70, 135, 66000, 369]

Mm = []
Zm = []
Rm = []
for t in range(len(Rd)):
  Rm.append(Rd[t]/Rd[t])
  Mm.append(Md[t]/Rd[t])
  Zm.append(Zd[t]/Rd[t])


list(map(report, [Mm, Zm, Rm]))
print(mean(Mm), mean(Zm), mean(Rm))

