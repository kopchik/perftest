#include "_perf.h"


int
perf_event_open(struct perf_event_attr *event, pid_t pid,
                int cpu, int group_fd, unsigned long flags)
{
    int ret;
    ret = syscall(__NR_perf_event_open, event, pid, cpu,
                   group_fd, flags);
    return ret;
}

void* mymalloc(size_t size) {
  void* ptr = malloc(size);
  assert(ptr);
  bzero(ptr, size);
  return ptr;
}

int open(pid_t pid) {
  struct perf_event_attr *pe;
  size_t pe_size;
  int fd, r;

  pe_size = sizeof(struct perf_event_attr);;

  pe = mymalloc(pe_size);
  pe->size = pe_size;
  pe->type = PERF_TYPE_HARDWARE;
  pe->config = PERF_COUNT_HW_INSTRUCTIONS;
  pe->disabled = 1;
  fd = perf_event_open(pe,   // counter
                       pid,  // pid
                        -1,  // cpu
                        -1,  // group_fd
                        0);  // flags
  if (fd < 0) { err(1, "perf_event_open"); }

  if ((r=ioctl(fd, PERF_EVENT_IOC_RESET, 0)) == -1)
    { err(1, "ioctl"); }
  if ((r=read(fd, &pe, sizeof(long long))) == -1)
    { err(1, "read"); }

  return fd;
}


int mainXXXX(int argc, char** argv) {
  pid_t pids[argc];
  size_t pids_num;
  char *err = NULL;

  for (int i=1; i<argc;i++) {
    pid_t pid = strtol(argv[i], &err, 10);
    assert(*err == '\0');
    assert((kill(pid, 0))); // check if process exists
    pids[i-1] = pid;
  }

  pids_num = argc - 1;
  for (int i=0; i<pids_num; i++) {
    printf("%d\n", pids[i]);
  }

  return 0;
}

