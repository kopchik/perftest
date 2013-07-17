#!/usr/bin/env python3

from bottle import abort, run, mount, request, load_app
from bottle import static_file, view
from bottle import get
from io import StringIO
from lib.utils import csv2dict
from tests.benches import benches


class String:
  def __init__(self):
    self.result = []

  def p(self, *args, end='', **kwargs):
    r = StringIO()
    print(*args, end=end, file=r, **kwargs)
    self.result += r.getvalue()

  def pn(self, *args, **kwargs):
    self.p(*args, end='\n', **kwargs)

  def __repr__(self):
    return "".join(self.result)


@get('/')
@view('main')
def show_table():
  result = StringIO()
  data = get_data(prefix="./results/u2/")
  print(table_tpl(data), file=result)
  return dict(body=result.getvalue())

@get('/static/<filename>')
def server_static(filename):
    return static_file(filename, root='./static')


def table_tpl(data):
  r = String()
  # preamble
  r.pn("<table border=1>")
  # header
  r.p("<tr><td>~</td>")
  for bench in benches:
    r.p("<td>{}</td>".format(bench))
  r.pn("</tr>\n")
  # table body
  for bg in benches:
    r.p("<tr><td>{}</td>".format(bg))
    for fg in benches:
      r.p("<td>{}</td>".format(data[bg,fg]))
    r.pn("</tr>\n")
  # epilogue
  r.pn("</table>")
  return r


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
      r[bg,fg] = "{:.1f}".format(v)
  return r


def get_degr(reference, sample):
  ref_ipc = reference['instructions']/reference['cycles']
  ipc = sample['instructions']/sample['cycles']
  return (1 - ipc/ref_ipc) * 100


if __name__ == '__main__':
  run(debug=True, interval=0.1, reloader=True)