./compare.py -p ./results/u2/ -b blosc -f pgbench  --show -o ~/github/perf2013paper/pic/blosc_pgbench.eps
./compare.py -p ./results/u2/ -b sdagp -f ffmpeg  --show -o ~/github/perf2013paper/pic/sdagp_ffmpeg.eps
./compare.py -p ./results/u2/ -b nginx -f matrix  --show -o ~/github/perf2013paper/pic/nginx_matrix.eps
./compare.py -p ./results/u2/ -b matrix -f sdag  --show -o ~/github/perf2013paper/pic/matrix_sdag.eps
./compare.py -f results/u2/{single/ffmpeg,double/integer/ffmpeg} --show -t 0.07 -o ~/github/perf2013paper/pic/u2_integer_ffmpeg.eps --title "Exinos 4412" -a "ffmpeg alone" "ffmpeg+integer"
./compare.py -f results/u2/{single/pgbench,double/sdagp/pgbench} --show -t 0.03 -o ~/github/perf2013paper/pic/u2_pgbench+sdagp.eps --title "Exinos 4412" -a "pgbench alone" "pgbench+sdagp"


# FX
./compare.py -f results/fx/single/{matrix,nginx,blosc,pgbench,sdagp,ffmpeg,wordpress,integer,sdag} -t 0.01 --show -k LLC-stores LLC-loads -t 0 -o ~/github/perf2013paper/pic/fx_brut_factors.eps  --title "AMD FX-8120"

# STABILITY
./stability_plot.py -f ./results/fx/stability/sleep_3/* \
  -o ~/github/perf2013paper/pic/fx_stab_sleep_3.eps


./stability_plot.py -f ./results/fx/stability/{sleep_0/sdagp,sleep_3/sdagp} \
  -o ~/github/perf2013paper/pic/fx_stab_sleep3_vs_sleep_0.eps

./stability_plot.py -f ./results/fx/stability/{sleep_0/sdagp,sleep_3/sdagp} \
  -o ~/github/perf2013paper/pic/fx_stab_sleep3_vs_sleep_0.eps \
  -a "sdagp (no interval)" "sdagp (3s interval)"


./compare.py -f results/fx/stability/matrix_{best,worst} --show -t 0