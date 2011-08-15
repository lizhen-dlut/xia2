#!/usr/bin/env python
# FormatCBFFull.py
#   Copyright (C) 2011 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# Base implementation of fullCBF format - as used with Dectris detectors
# amongst others - this will read the header and construct the full model,
# but will allow for extension for specific implementations of CBF.

import pycbf
import exceptions

from Toolkit.ImageFormat.FormatCBF import FormatCBF

class FormatCBFFull(FormatCBF):
    '''An image reading class for full CBF format images i.e. those from
    a variety of cameras which support this format.'''

    @staticmethod
    def understand(image_file):
        '''Check to see if this looks like an CBF format image, i.e. we can
        make sense of it. N.B. in situations where there is both a full and
        mini CBF header this will return a code such that this will be used
        in preference.'''

        if FormatCBF.understand(image_file) == 0:
            return 0

        header = FormatCBF.get_cbf_header(image_file)

        if not '_diffrn.id' in header and not '_diffrn_source' in header:
            return 0
        
        return 2

    def __init__(self, image_file):
        '''Initialise the image structure from the given file.'''

        assert(FormatCBFFull.understand(image_file) > 0)

        FormatCBF.__init__(self, image_file)

        return

    def _start(self):
        '''Open the image file as a cbf file handle, and keep this somewhere
        safe.'''

        FormatCBF._start(self)

        self._cbf_handle = pycbf.cbf_handle_struct()
        self._cbf_handle.read_file(self._image_file, pycbf.MSG_DIGEST)

        return

    def _xgoniometer(self):
        '''Return a working XGoniometer instance.'''

        return self._xgoniometer_factory.imgCIF_H(self._cbf_handle)

    def _xdetector(self):
        '''Return a working XDetector instance.'''

        return self._xdetector_factory.imgCIF_H(self._cbf_handle, 'unknown')

    def _xbeam(self):
        '''Return a working XBeam instance.'''

        return self._xbeam_factory.imgCIF_H(self._cbf_handle)

    def _xscan(self):
        '''Return a working XScan instance.'''

        return self._xscan_factory.imgCIF_H(self._image_file, self._cbf_handle)

if __name__ == '__main__':

    import sys

    for arg in sys.argv[1:]:
        print FormatCBFFull.understand(arg)
    

    


    
        



    

