#!/usr/bin/env python3

from collections import defaultdict
from pymongo import MongoClient
import argparse

def main():
  parser = argparse.ArgumentParser(description='Run experiments')
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--db', help="name of mongo database")
  group.add_argument('--list', const=True, action='store_const', help="list available databases")
  args = parser.parse_args()

  mongo_client = MongoClient()
  if args.list:
    return print(mongo_client.database_names())

  db = mongo_client[args.db]

  headers = []
  for evset in "basic partial full".split():

    for t in [1, 3, 10, 30, 90, 180, 300]:
      benches = defaultdict(lambda: defaultdict(list))
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


if __name__ == '__main__':
  main()