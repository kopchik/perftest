#!/usr/bin/env python
import numpy as np
import blosc

a = np.linspace(0, 100, 3e6)
bytes_array = a.tostring()

# 600 okay
for x in range(6000000):
    packed = blosc.pack_array(a)
    blosc.unpack_array(packed)
    del packed

