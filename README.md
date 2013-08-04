kvmtests
========

Some CPU tests. The code is "write-only", please do not use :)

Single benches
==============

## pgbench stability

~~~
for x in `seq 1020`; do sudo -u postgres pgbench -c 20 -s 10 -T 10 2>&1 | grep tps | grep excl | awk '{print $3}' >> ./pgbench_s03.csv; sleep 3; done
~~~

~~~
/bin/time -f %e /home/sources/kvmtests/benches/pyblosc.py -r 100 >/dev/null
~~~

## ux32vd experiments

~~~
sudo ./run_tests.py single --prefix ./results/ux32vd/ --debug -t single
sudo ./run_tests.py single --prefix ./results/ux32vd/ --debug -t double
~~~
