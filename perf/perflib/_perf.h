#include <stdlib.h>
#include <stdio.h>
#include <strings.h>
#include <assert.h>
#include <stdint.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <err.h>
#include <errno.h>
#include <signal.h>

#include <linux/perf_event.h>


int
perf_event_open(struct perf_event_attr *event, pid_t pid,
                int cpu, int group_fd, unsigned long flags);
void*
mymalloc(size_t size);