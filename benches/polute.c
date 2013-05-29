#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <err.h>

void *xcalloc(size_t n, size_t siz) {
  void *ptr = calloc(n, siz);
  if (!ptr) {
    err(6, "calloc failed"); }
  return ptr;
}

int main(int argc, char **argv) {
  int i,x,y;
  char mode[10];
  int *order;
  int *data;
  int dsize = 100*1024*1024;
  int cycles;
  int r;

  if (argc != 2) {
    errx(2, "please specify dsize=%%d,cycles=%%d,mode=%%s"); }
  if ((r=sscanf(argv[1], "dsize=%d,cycles=%d,mode=%s", &dsize, &cycles, mode)) != 3) {
    errx(4, "wrong parameters: read only %d params", r); }

  printf("dsize=%d,cycles=%d,mode=%s\n", dsize, cycles, mode);

  if (cycles <= 0) {
    errx(5, "cycles should be positive"); }

  if (dsize <= 0) {
    errx(5, "data array size should be positive"); }
  data = xcalloc(dsize, sizeof(int));
  for (i=0; i<dsize; i++) {
    data[i] = rand(); }


  if (strcmp(mode, "seq") == 0) {
    for (int x=0; x<cycles; x++) {
      for (i=0; i<dsize; i++) {
        int val = data[i];}}}
  else if (strcmp(mode, "rand") == 0) {
    order = xcalloc(dsize, sizeof(int));
    srand(time(NULL));
    /* init order array */
    for (i=0; i<dsize; i++) {
      order[i] = rand() % dsize; }
    /* traverse `cycles' times */
    for (int x=0; x<cycles; x++) {
      for (i=0; i<dsize; i++) {
        int val = data[order[i]];}}}
  else {
      errx(3, "unknown mode %s", mode);}
  //printf("done\n");



  return 0;
}
