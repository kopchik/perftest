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
  int osize = 1*1024*1024;
  int *data;
  int dsize = 100*1024*1024;
  int r;

  if (argc != 2) {
    errx(2, "please specify dsize=%%d,osize=%%d,mode=%%s"); }
  if ((r=sscanf(argv[1], "dsize=%d,osize=%d,mode=%s\n", &dsize, &osize, mode)) != 3) {
    errx(4, "wrong parameters: read only %d chars", r); }


  if (dsize <= 0) {
    errx(5, "data array size should be positive"); }
  printf("size of data array: %d\n", dsize);
  data = xcalloc(dsize, sizeof(int));
  for (i=0; i<dsize; i++) {
    data[i] = rand(); }

  if (osize <= 0) {
    errx(5, "order array size should be positive"); }
  printf("size of order array: %d\n", osize);
  order = xcalloc(osize, sizeof(int));
  if (strcmp(mode, "seq") == 0) {
    for (i=0; i<osize; i++) {
      order[i] = i % dsize; }}
  else if (strcmp(mode, "rand") == 0) {
    srand(time(NULL));
    for (i=0; i<osize; i++) {
      order[i] = rand() % dsize; }}
  else {
      errx(3, "unknown mode %s", mode);
    }
  printf("done\n");


  while (1) {
    for (i=0; i<osize; i++) {
      x = data[order[i]];
    }
  }

  return 0;
}