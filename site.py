#!/usr/bin/env python3

from bottle import abort, run, mount, request, load_app, default_app as app
from bottle import static_file, view
from bottle import get, MakoTemplate
from lib.utils import csv2dict
from tests.benches import benches

MakoTemplate.defaults['benches'] = sorted(benches)


@get('/')
@view('main')
def show_table():
  experiments = []
  # u2
  data = get_data(prefix="./results/u2/")
  experiments += [dict(
    data=data,
    imgpath="/static/u2",
    title="Samsung Exynos-4412 (Odroid-U2 board)")]
  # fx
  data = get_data(prefix="./results/fx", sibling=True)
  experiments += [dict(
    data=data,
    imgpath="/static/fx_near",
    title="AMD FX-8120 (sibling cores)")]
  data = get_data(prefix="./results/fx", sibling=False)
  experiments += [dict(
    data=data,
    imgpath="/static/fx_far",
    title="AMD FX-8120 (distant cores)")]
  ## ux32vd
  #data = get_data(prefix="./results/ux32vd/")
  #experiments += [dict(
  #    data=data,
  #    imgpath="/static/ux32vd",
  #    title="Intel i7-3517u@1.7GHz (asus ux32vd)",
  #    annotation="""O_O""")]
  ## panda
  #data = get_data(prefix="./results/panda/notp/")
  #experiments += [dict(
  #    data=data,
  #    imgpath="/static/panda",
  #    title="TI OMAP 4460 (PandaBoard-ES)",
  #    annotation="""The hardware performance counters didn't work
  #    well on this board. This data cannot be trust.""")]

  return dict(experiments=experiments)

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
      r[bg,fg] = get_degr(reference, sample)
  return r


def get_degr(reference, sample):
  ref_ipc = reference['instructions']/reference['cycles']
  try:
    ipc = sample['instructions']/sample['cycles']
  except KeyError:
    return -666
  return (1 - ipc/ref_ipc) * 100


if __name__ == '__main__':
  run(debug=True, server='gunicorn', interval=0.1, host='localhost', port=8080, reloader=True)
