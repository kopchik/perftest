import waflib.Configure
waflib.Configure.autoconfig = True


def options(opt):
  opt.load('compiler_c')


def configure(conf):
  conf.env["CC"] = ["clang"]
  conf.load('compiler_c')
  conf.env.CFLAGS = ['-ggdb', '-std=gnu99']
  if 0:
    conf.env.CFLAGS += ['-fmudflap']
    conf.env.LINKFLAGS = ['-lmudflap']
    conf.env.SHLIB_MARKER = '-Wl,-e,main'


def build(bld):
  #bld.program(source='perf_api.c', target='perf_api')
  bld.shlib(source='perf_api.c', target='perf_api')
