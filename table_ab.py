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
for bg in single:
  for fg in single:
    p = csv2dict(PATH+'/double/'+bg+'/'+fg)
    inps = p['instructions'] / p['cycles']
#print(single)
