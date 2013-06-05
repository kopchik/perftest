int main(void) {
  int a,b,c,d=0;
  int i,j;
  for (j=0;j < 10*1000*1000;j++) {
    a = 1;
    b = 3;
    c = 4;
    d = 5;
    for (i=0; i < 100; i++) {
      a = a + 2*b + 3*c + 4*d;
      b = c + b/d;
    }
  }
  return 0;
}
