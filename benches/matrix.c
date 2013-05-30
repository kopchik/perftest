#include <stdio.h>
#include <gsl/gsl_blas.h>
#include <err.h>


void *xcalloc(size_t n, size_t siz) {
  void *ptr = calloc(n, siz);
  if (!ptr) {
    err(6, "calloc failed"); }
  return ptr;
}


int
main (int argc, char *argv[])
{
  if (argc != 2) {
      errx(2, "please specify size"); }
  int size = atoi(argv[1]);

  printf("size: %d\n", size);
  double *a = xcalloc(size*size, sizeof(double));
  double *b = xcalloc(size*size, sizeof(double));
  double *c = xcalloc(size*size, sizeof(double));

  for (int i=0; i< size*size; i++) {
    a[i] = 1;
    b[i] = 1;
    c[i] = 0;
  }

  gsl_matrix_view A = gsl_matrix_view_array(a, size, size);
  gsl_matrix_view B = gsl_matrix_view_array(b, size, size);
  gsl_matrix_view C = gsl_matrix_view_array(c, size, size);

  gsl_blas_dgemm (CblasNoTrans, CblasNoTrans,
                  1.0, &A.matrix, &B.matrix,
                  0.0, &C.matrix);

  //printf ("[ %g, %g\n", c[0], c[1]);
  //printf ("  %g, %g ]\n", c[2], c[3]);

  free(a);
  free(b);
  free(c);
  return 0;
}

