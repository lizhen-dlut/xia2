#!/usr/bin/env python
# FormatTIFF.py
#   Copyright (C) 2011 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# Implementation of an ImageFormat class to read TIFF format image but not -
# in the first instance - actually provide a full image representation. This
# is simply there to set everything up for the ADSC and Rigaku Saturn image
# readers which really will acquire the full image including header information
# and generate the experimental model representations.

from Format import Format
from FormatTiffHelpers import read_basic_tiff_header
from FormatTiffHelpers import LITTLE_ENDIAN
from FormatTiffHelpers import BIG_ENDIAN

class FormatTIFF(Format):
    '''An image reading class for TIFF format images i.e. those from Dectris
    and Rayonix, which start with a standard TIFF header (which is what is
    handled here) and have their own custom header following, which must
    be handled by the inheriting subclasses.'''

    @staticmethod
    def understand(image_file):
        '''Check to see if this looks like an TIFF format image, i.e. we can
        make sense of it.'''

        try:
            width, height, depth, header, order = read_basic_tiff_header(
                image_file)
            return 1
        
        except:
            pass

        return 0

    def __init__(self, image_file):
        '''Initialise the image structure from the given file.'''
        
        assert(FormatTIFF.understand(image_file) > 0)

        Format.__init__(self, image_file)

        return

    def _start(self):
        '''Open the image file, read the image header, copy it into memory
        for future inspection.'''

        width, height, depth, header, order = read_basic_tiff_header(
            image_file)

        self._tiff_width = width
        self._tiff_height = height
        self._tiff_depth = depth // 8
        self._tiff_header_bytes = open(image_file, 'rb').read(header)
        self._tiff_byte_order = order

        return


    

