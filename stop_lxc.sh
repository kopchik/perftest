#!/bin/bash

for lxc in `lxc-ls`; do
    sudo lxc-destroy -n $lxc -f
done
