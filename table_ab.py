#!/usr/bin/env python3
import os
PATH="./results/fx/cc_auto/"

def csv2dict(f):
  d = {}
  with open(f) as fd:
    for l in fd.readlines():
      if l.startswith('#') or l.isspace():
        continue
      l = l.strip()
      v,k, *rest = l.split(',')
      if k in ['cpu-clock', 'task-clock']: continue
      d[k] = int(v)
  return d

single = {}
for name in os.listdir(PATH+'/single/'):
  p = csv2dict(PATH+'/single/'+name)
  inps = p['instructions'] / p['cycles']
  single[name] = inps

double = {}
print(" &".join(sorted(single)), "\\\\")
for bg in sorted(single):
  print("{:12}".format(bg), end='')
  for fg in sorted(single):
    p = csv2dict(PATH+'/double/'+bg+'/'+fg)
    inps = p['instructions'] / p['cycles']
    ratio = inps/single[fg]
    double[bg,fg] = ratio
    print("& {:4.1f}".format((1-ratio)*100), end=' ')
  print(' \\\\')

print(double['integer','blosc'])
