#!/bin/bash
benches=('nginx' 'sdagp' 'integer' 'pgbench' 'matrix' 'ffmpeg' 'wordpress' 'blosc' 'sdag')


regen() {
src=$1
dst=$2
near=$3
for bg in "${benches[@]}"; do
  for fg in "${benches[@]}"; do
    mkdir -p "${dst}/${bg}/"
    if [ -n "$near" ]; then
      ./compare.py -s -p $src -f $fg -b $bg -o "${dst}/${bg}/${fg}.png"
    else
      ./compare.py    -p $src -f $fg -b $bg -o "${dst}/${bg}/${fg}.png"
    fi
  done
done
}

# regen "./results/panda/notp/" "./static/panda/" &
regen "./results/u2/" "./static/u2/" &
# regen "./results/fx/cc_auto/notp/" "./static/fx_far/" &
# regen "./results/fx/cc_auto/notp/" "./static/fx_near/" "near" &