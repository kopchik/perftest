#!/bin/bash
benches=('nginx' 'sdagp' 'integer' 'pgbench' 'matrix' 'ffmpeg' 'wordpress' 'blosc' 'sdag')


for bg in "${benches[@]}"; do
  for fg in "${benches[@]}"; do
    mkdir -p "static/u2/${bg}/"
    ./compare.py -p "results/u2/" -f $fg -b $bg -o "static/u2/${bg}/${fg}.png"
  done
done

