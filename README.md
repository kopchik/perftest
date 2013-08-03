kvmtests
========

Some CPU tests. The code is "write-only", please do not use :)

Single benches
==============

## pgbench

~~~
for x in `seq 1020`; do sudo -u postgres pgbench -c 20 -s 10 -T 10 2>&1 | grep tps | grep excl | awk '{print $3}' >> ./pgbench_s03.csv; sleep 3; done
~~~
