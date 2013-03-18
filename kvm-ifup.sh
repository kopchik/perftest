#!/bin/sh

#TODO: read bridge name from env
SUDO=''
if [ `id -u` != "0" ]; then
    SUDO=sudo
fi

if [ -z "$BRIDGE" ]; then
  BRIDGE=intbr
fi
nic=$1

#$SUDO ifconfig $nic 0.0.0.0 up
$SUDO ip link set $nic up
$SUDO brctl addif $BRIDGE $nic