#!/bin/sh

#TODO: read bridge name from env
SUDO=''
if [ `id -u` != "0" ]; then
    SUDO=sudo
fi

switch=intbr
nic=$1

#$SUDO ifconfig $nic 0.0.0.0 up
$SUDO ip link set $nic up
$SUDO brctl addif $switch $nic
