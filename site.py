#!/usr/bin/env python3

from bottle import abort, run, mount, request, load_app
from bottle import static_file, view
from bottle import get, MakoTemplate
from lib.utils import csv2dict
from tests.benches import benches

MakoTemplate.defaults['benches'] = sorted(benches)


@get('/')
@view('main')
def show_table():
  data = get_data(prefix="./results/u2/")
  return dict(data=data)

@get('/static/<filename:path>')
def server_static(filename):
    return static_file(filename, root='./static')


def get_data(prefix, sibling=True):
  r = {}
  ref_prefix = "{prefix}/single/".format(prefix=prefix)
  if sibling: sample_prefix = "{prefix}/double/".format(prefix=prefix)
  else:       sample_prefix = "{prefix}/double_far/".format(prefix=prefix)

  for bg in benches:
    for fg in benches:
      reference = csv2dict(ref_prefix+"{fg}".format(fg=fg))
      sample = csv2dict(sample_prefix+"/{bg}/{fg}".format(bg=bg,fg=fg))
      v = get_degr(reference, sample)
      r[bg,fg] = get_degr(reference, sample)
  return r


def get_degr(reference, sample):
  ref_ipc = reference['instructions']/reference['cycles']
  ipc = sample['instructions']/sample['cycles']
  return (1 - ipc/ref_ipc) * 100


if __name__ == '__main__':
  run(debug=True, interval=0.1, reloader=True)