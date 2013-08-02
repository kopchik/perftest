./compare.py -p ./results/u2/ -b blosc -f pgbench  --show -o ~/github/perf2013paper/pic/blosc_pgbench.eps
./compare.py -p ./results/u2/ -b sdagp -f ffmpeg  --show -o ~/github/perf2013paper/pic/sdagp_ffmpeg.eps
./compare.py -p ./results/u2/ -b nginx -f matrix  --show -o ~/github/perf2013paper/pic/nginx_matrix.eps
./compare.py -p ./results/u2/ -b matrix -f sdag  --show -o ~/github/perf2013paper/pic/matrix_sdag.eps

