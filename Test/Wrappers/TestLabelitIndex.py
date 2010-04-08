#!/usr/bin/env python
# TestLabelitIndex.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is 
#   included in the root directory of this package.
#
# 2nd June 2006
# 
# Unit tests to ensure that the LabelitIndex wrapper is behaving
# properly.
# 
# 

import os, sys

if not os.environ.has_key('XIA2_ROOT'):
    raise RuntimeError, 'XIA2_ROOT not defined'

sys.path.append(os.path.join(os.environ['XIA2_ROOT']))

from Wrappers.Labelit.LabelitIndex import LabelitIndex
import unittest

from Handlers.Streams import streams_off

streams_off()

# this should be placed in a gwmath module or something...

def nint(a):
    b = int(a)
    if a - b > 0.5:
        b += 1
    return b

class TestLabelitIndex(unittest.TestCase):

    def setUp(self):
        pass

    def testtetragonal(self):
        '''A test to see if the indexing works when it should.'''

        ls = LabelitIndex()

        directory = os.path.join(os.environ['XIA2_ROOT'],
                                 'Data', 'Test', 'Images')

        ls.setup_from_image(os.path.join(directory, '12287_1_E1_001.img'))
        ls.add_indexer_image_wedge(1)
        ls.add_indexer_image_wedge(90)
        ls.index()

        # test the refined parameters
        self.assertEqual(nint(ls.get_indexer_distance()), 170)

        beam = ls.get_indexer_beam()
        
        self.assertEqual(nint(beam[0]), 109)
        self.assertEqual(nint(beam[1]), 105)

        return

    def testsetfalsebeam(self):
        '''A test to see if the indexing works when it should.'''

        # FIXME this no longer fails! :o(
        # LABELIT Indexing results:
        # Beam center x   92.94mm, y   87.49mm, distance  169.69mm ; \
        # 60%(POOR) mosaicity=1.50 deg.
        # Solution  Metric fit  rmsd  #spots  crystal_system   unit_cell
        # :)   2     0.3440 dg 4.354    119    monoclinic mC  \
        # 100.66   7.57  50.30  90.00 95.46  90.00    38145
        # :)   1     0.0000 dg 4.365    152     triclinic aP    \
        # 7.56  49.82  50.39  95.39 90.02  94.01    18856

        ls = LabelitIndex()

        directory = os.path.join(os.environ['XIA2_ROOT'],
                                 'Data', 'Test', 'Images')

        ls.setup_from_image(os.path.join(directory, '12287_1_E1_001.img'))

        # this is not needed
        ls.add_indexer_image_wedge(1)
        ls.add_indexer_image_wedge(90)

        # set the beam to something totally false
        ls.set_beam((90.0, 90.0))

        self.assertRaises(RuntimeError, ls.index)

        return


if __name__ == '__main__':
    unittest.main()


    

