#!/usr/bin/bash

NUM=4
DEST=/home/perf
TEMPLATE=/home/perftemplate
OPTIND=1
while getopts "n:p:s:" opt; do
  case $opt in
    n)
        NUM=$OPTARG
        ;;
    d)
        DEST=$OPTARG
        ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        ;;       
  esac
done
# shift $((OPTIND-1))

for x in `seq 0 $((NUM-1))`; do
  echo btrfs subvolume delete ${DEST}${x}
  echo btrfs subvolume snapshot ${TEMPLATE} ${DEST}${x}
done

sync