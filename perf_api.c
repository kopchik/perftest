#define _GNU_SOURCE
#include <linux/perf_event.h>
#include <sys/syscall.h>
#include <inttypes.h>
#include <strings.h>
#include <stddef.h>
#include <unistd.h>
#include <stdint.h>
#include <stdlib.h>
#include <stropts.h>
#include <fcntl.h>
#include <err.h>
#include "myassert.h"
//const char interpreter[] __attribute__((section(".interp"))) = "/lib/ld-linux.so.2";

#define MAXNUM 10

#define debug( ...) \
    do {fprintf(stderr, _FILEPOS_ __VA_ARGS__); \
        fprintf(stderr, "\n"); \
       } while (0)

#define error(label, ...) \
    do {saved_errno = errno; \
        fprintf(stderr, _FILEPOS_ __VA_ARGS__); \
        fprintf(stderr, "\n"); \
        goto label; \
       } while (0)


typedef struct CGEvents {
  int nr;
  int fds[MAXNUM];
  int result_size;
  struct result {
    uint64_t nr;
    uint64_t time_enabled;
    uint64_t time_running;
    // struct values{
    //  uint64_t value;
    // } values[MAXNUM];
    uint64_t values[MAXNUM];
  } result;
} CGEvents;

typedef struct CGArray {
  int nr;
  int cpus[MAXNUM];
  CGEvents *events[MAXNUM];
} CGArray;

int sys_perf_event_open(struct perf_event_attr *attr,
              pid_t pid, int cpu, int group_fd,
              unsigned long flags) {
    return syscall(SYS_perf_event_open, attr, pid, cpu,
               group_fd, flags);
}

struct perf_event_attr *NewEvent(void) {
    struct perf_event_attr *event;
    size_t size = sizeof(struct perf_event_attr);
    event = malloc(size);
    myassert2(event, "malloc()");
    bzero(event, size);
    event->size = sizeof(struct perf_event_attr);
    return event;
}

struct perf_event_attr *HWEvent(void) {
    struct perf_event_attr *event = NewEvent();
    event->type = PERF_TYPE_HARDWARE;
    return event;
}

struct perf_event_attr *CyclesEvent(void) {
    struct perf_event_attr *event = HWEvent();
    event->config = PERF_COUNT_HW_CPU_CYCLES;
    return event;
}

struct perf_event_attr *InstrEvent(void) {
    struct perf_event_attr *event;
    event = HWEvent();
    event->config = PERF_COUNT_HW_INSTRUCTIONS;
    return event;
}

CGEvents *cgev_create(char *path, char *_evsel, int cpu) {
  int nr = 0;
  int fd, group_fd=-1;
  CGEvents *events;
  struct perf_event_attr *perf_event;
  int saved_errno;

  /* open cgroup's dir fd */
  int dir_fd;
  debug("enabling monitoring for %s", path);
  dir_fd = open(path, O_RDONLY);
  if (dir_fd == -1) {
    error(CANT_OPEN_DIRECTORY, "can't open directory: errno %d", errno); }

  /* alloc mem for structure */
  events = malloc(sizeof(CGEvents));
  myassert2(events, "malloc()");
  bzero(events, sizeof(CGEvents));


  /* parse events */
  char *r, *saveptr;
  char *evsel = strdup(_evsel);
  myassert2(evsel, "strdup()");

  r = strtok_r(evsel, ",", &saveptr);
  myassert(r, "please select at least one event");
  while(r != NULL) {
    myassert2(nr < MAXNUM, "too many events");
    // printf("result is \"%s\"\n", r);
    if (strcmp(r, "instructions") == 0) {
      perf_event = InstrEvent();}
    else if (strcmp(r, "cycles") == 0) {
      perf_event = CyclesEvent();}
    else {
      errx(2, "unknown event %s", r);}
    perf_event->read_format  = PERF_FORMAT_GROUP;
    perf_event->read_format |= PERF_FORMAT_TOTAL_TIME_ENABLED;
    perf_event->read_format |= PERF_FORMAT_TOTAL_TIME_RUNNING;
    fd = sys_perf_event_open(perf_event, dir_fd, cpu, group_fd, PERF_FLAG_PID_CGROUP);
    if (fd == -1) {
      error(PERF_OPEN_ERR, "sys_perf_event_open(): errno %d", errno);}
    events->fds[nr] = fd;
    free(perf_event);
    if (group_fd == -1) {
      group_fd = fd;}
    nr++;
    r = strtok_r(NULL, ",", &saveptr);
  }
  free(evsel);

  events->nr = nr;

  //events->fds = calloc(sizeof(int), nr);
  myassert2(events->fds, "calloc()");
  //memcpy(events->fds, fds, sizeof(int)*nr);

  events->result_size = sizeof(CGEvents) - offsetof(CGEvents, result);

  return events;

  PERF_OPEN_ERR:
    //TODO: check this
    for (int i=0; i<nr; i++) {
      printf("closing fd");
      close(events->fds[i]);}
    free(events);
    free(evsel);
  CANT_OPEN_DIRECTORY:
    errno = saved_errno;
  return NULL;
}

void cgev_reset(CGEvents *events) {
      int group_fd = events->fds[0];
      ioctl(group_fd, PERF_EVENT_IOC_DISABLE, 0);
      for (int i=0; i<events->nr; i++) {
        ioctl(events->fds[i], PERF_EVENT_IOC_RESET, 0);}
      ioctl(group_fd, PERF_EVENT_IOC_ENABLE, 0);

}

void cgev_read(CGEvents *events) {
  int res = read(events->fds[0], (&events->result), events->result_size);
  myassert2(res != -1, "read()");
  printf("perf enabled time: %.3f\n",
    (double) events->result.time_running / events->result.time_enabled);
  //cgev_reset(events);
}

void cgev_destroy(CGEvents *events) {
  for (int i=0; i<events->nr; i++) {
    close(events->fds[i]); }

  free(events); //TODO
}

CGArray *cga_create(char *path, char *evsel, char *_cpusel) {
  char *cpusel;
  int cpu;
  CGArray *cga;

  cpusel = strdup(_cpusel);
  myassert2(_cpusel, "strdup()");
  cga = malloc(sizeof(CGArray));
  myassert2(cga, "malloc()");

  cga->nr = 0;

  char *r, *saveptr;
  r = strtok_r(cpusel, ",", &saveptr);
  myassert(r, "please specify at least one cpu to monitor");
  while(r != NULL) {
    myassert2(cga->nr < MAXNUM, "too many cpus");
    printf("result is \"%s\"\n", r);
    cpu = atoi(r);  // TODO: improve error handling here
    cga->events[cga->nr] = cgev_create(path, evsel, cpu);
    printf("created ev: %p\n", cga->events[cga->nr]);
    cga->cpus[cga->nr] = cpu;
    cga->nr++;
    r = strtok_r(NULL, ",", &saveptr);
  }
  free(cpusel);

  return cga;
}

void cga_destroy(CGArray *cga) {
  for (int i=0; i<(cga->nr); i++) {
    cgev_destroy(cga->events[i]);}
  //free(cga->events);
  //free(cga->cpus);
  free(cga);
}

void cga_read(CGArray *cga) {
  int i, j;
  CGEvents *ev;
  for (int i=0; i<(cga->nr); i++) {
    cgev_read(cga->events[i]);}

  for (int i=0; i<(cga->nr); i++) {
    ev=cga->events[i];
    printf("ev: %p, nr=%d\n", ev, ev->nr);
    for (int j=0; j<(ev->nr); j++) {
      printf("%"PRIu64" ", ev->result.values[j]);
    }
  }
  printf("\n");
}


void cga_reset(CGArray *cga) {
    CGEvents *events;
    int group_fd;

    for (int i=0; i<cga->nr; i++) {
      events = cga->events[i];
      cgev_reset(events);
    }
}

int _main(void) {
  // CGEvents *cgev;
  // cgev = cgev_create("/sys/fs/cgroup/perf_event/crm/", /*events*/ "instructions,", /*cpu*/ 0);
  // for(int i=0;i<10;i++) {
  //  cgev_read(cgev);
  //  // printf("%"PRIu64" %"PRIu64" %"PRIu64" %"PRIu64" \n",
  //  //  cgev->result.values[0].value, result.time_enabled, result.time_running, result.id);
  //  printf("%"PRIu64"\n", cgev->result.values[0].value);
  //  sleep(1);
  // }
  // cgev_destroy(cgev);
  // return 0;


  CGArray *cga;
  cga = cga_create("/sys/fs/cgroup/perf_event/crm/", /*events*/ "instructions,cycles", /*cpus*/ "0,1");
  for(int i=0; i<10; i++) {
    //sleep(1);
    cga_read(cga);}
  cga_destroy(cga);

  return 0;
}
