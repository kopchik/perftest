./compare.py -p ./results/u2/ -b blosc -f pgbench  --show -o ~/github/perf2013paper/pic/blosc_pgbench.eps
./compare.py -p ./results/u2/ -b sdagp -f ffmpeg  --show -o ~/github/perf2013paper/pic/sdagp_ffmpeg.eps
./compare.py -p ./results/u2/ -b nginx -f matrix  --show -o ~/github/perf2013paper/pic/nginx_matrix.eps
./compare.py -p ./results/u2/ -b matrix -f sdag  --show -o ~/github/perf2013paper/pic/matrix_sdag.eps


# STABILITY
./stability_plot.py -f ./results/fx/stability/sleep_3/* \
  -o ~/github/perf2013paper/pic/fx_stab_sleep_3.eps


./stability_plot.py -f ./results/fx/stability/{sleep_0/sdagp,sleep_3/sdagp} \
  -o ~/github/perf2013paper/pic/fx_stab_sleep3_vs_sleep_0.eps

./stability_plot.py -f ./results/fx/stability/{sleep_0/sdagp,sleep_3/sdagp} \
  -o ~/github/perf2013paper/pic/fx_stab_sleep3_vs_sleep_0.eps \
  -a "sdagp (no interval)" "sdagp (3s interval)"


./compare.py -f results/fx/stability/matrix_{best,worst} --show -t 0