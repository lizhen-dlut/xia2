#!/usr/bin/env python
# rebatch.py
# 
#   Copyright (C) 2011 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is 
#   included in the root directory of this package.
# 
# Replacement for CCP4 program rebatch, using cctbx Python.
# 

import os
import sys

from iotbx import mtz
from cctbx.array_family import flex

def rebatch(hklin, hklout, first_batch):
    '''Need to implement: include batch range, exclude batches, add N to
    batches, start batches at N.'''

    mtz_obj = mtz.object(file_name = hklin)

    batch_column = None
    batch_dataset = None

    for crystal in mtz_obj.crystals():
        for dataset in crystal.datasets():
            for column in dataset.columns():
                if column.label() == 'BATCH':
                    batch_column = column
                    batch_dataset = dataset

    if not batch_column:
        raise RuntimeError, 'no BATCH column found in %s' % hklin

    batch_column_values = batch_column.extract_values(
        not_a_number_substitute = -1)

    valid = flex.bool()

    # modify batch columns, and also the batch headers

    if first_batch != None:
        offset = first_batch - min(batch_column_values)
        batch_column_values = batch_column_values + offset

        for batch in mtz_obj.batches():
            batch.set_num(int(batch.num() + offset))
            
    # done modifying
    
    batch_column.set_values(values = batch_column_values,
                            selection_valid = valid)

    # and write this lot out as hklout
    
    mtz_obj.write(file_name = hklout)

if __name__ == '__main__':

    import sys

    hklin = sys.argv[1]
    hklout = 'arse.mtz'

    rebatch(hklin, hklout, first_batch = 1001)
