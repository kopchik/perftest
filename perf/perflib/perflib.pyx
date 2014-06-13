from cpython.mem cimport PyMem_Malloc, PyMem_Free
from libc.stdint cimport int64_t, uint32_t, uint64_t
from posix.unistd cimport pid_t, useconds_t, read, usleep
from posix.ioctl cimport ioctl
from libc.signal cimport SIGCONT, SIGSTOP
from cython cimport sizeof
import os

cdef extern from "signal.h" nogil:
  int kill(pid_t pid, int sig) except -1

cdef extern from "linux/perf_event.h":
  cdef struct perf_event_attr:
    uint32_t type
    uint32_t size
    uint64_t config
    uint64_t disabled
    uint64_t read_format

  cdef enum perf_type_id:
    PERF_TYPE_HARDWARE
    PERF_COUNT_HW_INSTRUCTIONS
    PERF_COUNT_HW_CPU_CYCLES
  cdef int PERF_EVENT_IOC_RESET
  cdef int PERF_FORMAT_GROUP
  cdef int PERF_IOC_FLAG_GROUP
  cdef int PERF_FORMAT_TOTAL_TIME_ENABLED
  cdef int PERF_FORMAT_TOTAL_TIME_RUNNING
  cdef int PERF_EVENT_IOC_ENABLE

cdef extern from "_perf.h":
  void* mymalloc(size_t size)
  int perf_event_open(perf_event_attr *event, pid_t pid,
                  int cpu, int group_fd, unsigned long flags) except -1


cdef struct Result:
  uint64_t nr
  uint64_t time_enabled
  uint64_t time_running
  uint64_t instr
  uint64_t cycles


cdef class Task:
  cpdef pid_t pid
  cdef int ifd, cfd

  def __cinit__(self, pid_t pid=0):
    cdef int pe_size
    cdef perf_event_attr *pe

    kill(pid, 0)
    self.pid = pid

    pe_size = sizeof(perf_event_attr)
    pe = <perf_event_attr*>mymalloc(pe_size)

    pe.size = pe_size
    pe.type = PERF_TYPE_HARDWARE
    pe.disabled = 1
    pe.read_format = PERF_FORMAT_GROUP | PERF_FORMAT_TOTAL_TIME_ENABLED | PERF_FORMAT_TOTAL_TIME_RUNNING
    pe.config = PERF_COUNT_HW_INSTRUCTIONS
    self.ifd = perf_event_open(pe, pid, -1, -1, 0)

    pe.config = PERF_COUNT_HW_CPU_CYCLES
    self.cfd = perf_event_open(pe, pid, -1, self.ifd, 0)

    r = ioctl(self.ifd, PERF_EVENT_IOC_ENABLE, PERF_IOC_FLAG_GROUP)
    assert r != -1, "ioctl PERF_EVENT_IOC_ENABLE failed"

  cpdef measure(self, double interval):
    cdef Result cnts
    cdef int r

    r = ioctl(self.ifd, PERF_EVENT_IOC_RESET, PERF_IOC_FLAG_GROUP)
    assert r != -1, "ioctl PERF_EVENT_IOC_RESET failed"
    usleep(<useconds_t>(interval*(10.0**6)))  # convert seconds to microseconds
    r = read(self.ifd, &cnts, sizeof(cnts))
    assert r == sizeof(cnts)
    assert cnts.time_running == cnts.time_enabled
    return (cnts.instr, cnts.cycles)

  cpdef measurex(self, double interval, int num):
    return [self.measure(interval) for _ in range(num)]

  def freeze(self, tasks):
    for t in tasks:
      if t == self: continue
      t.stop()

  def defrost(self, tasks):
    for t in tasks:
      t.cont()

  cpdef stop(self):
    kill(self.pid, SIGSTOP)

  cpdef cont(self):
    kill(self.pid, SIGCONT)