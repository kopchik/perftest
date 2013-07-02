#!/usr/bin/bash

NUM=4
DEST=/home/perf
TEMPLATE=/home/perftemplate
OPTIND=1
IP="172.16.5.1"
while getopts "n:d:t:i:" opt; do
  case $opt in
    n)  NUM=$OPTARG;;
    d)  DEST=$OPTARG;;
    t)  TEMPLATE=$OPTARG;;
    \?) echo "Invalid option: -$OPTARG" >&2;;
  esac
done

for x in `seq 0 $((NUM-1))`; do
  name=`basename ${DEST}${x}`
  dst=${DEST}${x}
  lxc-destroy -n $name
  btrfs subvolume delete ${dst}
  btrfs subvolume snapshot ${TEMPLATE} ${dst}
  lxc-create -t `pwd`/configs/lxc-template.py -n $name -- --addr=${IP}${x}
done

sync