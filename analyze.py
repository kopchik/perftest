#!/usr/bin/env python3

from collections import defaultdict
from pymongo import MongoClient

if __name__ == '__main__':
  mongo_client = MongoClient()
  db = mongo_client.perf

  headers = []
  for evset in "basic partial full".split():
    benches = defaultdict(lambda: defaultdict(list))

    for t in [1, 3, 10, 30]:#, 90, 180, 300]:
      colName = "stab_%s_%ss" % (evset, t)
      print("===%s==="%colName)
      headers += [colName]
      col = db[colName]
      for r in col.find():
        n = r['ann']
        for k,v in r.items():
          benches[n][k] += [v]
    for k,r in benches.items():
      print(r['ann'])
      for k,v in [('instructions', r['instructions'])]: #r.items():
        print(k, ["{:.3f}".format(v) for v in v if isinstance(v, (int,float))])