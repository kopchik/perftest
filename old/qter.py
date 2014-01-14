#!/usr/bin/env python3

a = 5
d = 4

i = 0
q = []

class Q:
  def __init__(self):
    self.l = []
    self.adds = 0
    self.pops = 0
    self.ticks = 0
  def append(self, e):
    self.l.append(e)
    self.adds += 1
  def tick(self):
    self.ticks += 1
  def pop(self):
    if self.l:
      self.l.pop()
    self.pops += 1

  def __repr__(self):
    return "Q(%s, adds=%s, pops=%s)" % (self.l, self.adds, self.pops)
q = Q()
while True:
  i += 1
  if not i%a:
    q.append(1)
  if not i%d:
    q.pop()
  q.tick()
  if i > 10000:
    break
print(q)
