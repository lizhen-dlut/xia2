#!/usr/bin/env python
# CommandLine.py
# Maintained by G.Winter
# 12th June 2006
# 
# A handler for all of the information which may be passed in on the command
# line. This singleton object should be able to handle the input, structure
# it and make it available in a useful fashion.
# 
# This is a hook into a global data repository.
# 
# Modification log:
# 
# 21/JUN/06 - Added in parsing of image (passed in on -image token, or
#             last token) to template & directory to work with. Note 
#             well - I need to think more carefully about this in the
#             future, though this solution may scale...
# 

import sys
import os
import exceptions

if not os.environ.has_key('DPA_ROOT'):
    raise RuntimeError, 'DPA_ROOT not defined'
if not os.environ.has_key('XIA2CORE_ROOT'):
    raise RuntimeError, 'XIA2CORE_ROOT not defined'

if not os.environ['DPA_ROOT'] in sys.path:
    sys.path.append(os.path.join(os.environ['DPA_ROOT']))

from Schema.Object import Object
from Experts.FindImages import image2template_directory

class _CommandLine(Object):
    '''A class to represent the command line input.'''

    def __init__(self):
        '''Initialise all of the information from the command line.'''

        Object.__init__(self)

        try:
            self._read_beam()
        except:
            raise RuntimeError, self._help_image()

        try:
            self._read_image()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_image(), str(e))

        return

    # command line parsers, getters and help functions.

    def _read_beam(self):
        '''Read the beam centre from the command line.'''

        index = -1

        try:
            index = sys.argv.index('-beam')
        except ValueError, e:
            # the token is not on the command line
            self.write('No beam passed in on the command line')
            self._beam = (0.0, 0.0)
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        try:
            beam = sys.argv[index + 1].split(',')
        except IndexError, e:
            raise RuntimeError, '-beam correct use "-beam x,y"'

        if len(beam) != 2:
            raise RuntimeError, '-beam correct use "-beam x,y"'

        self.write('Beam passed on the command line: %7.2f %7.2f' % \
                   (float(beam[0]), float(beam[1])))

        self._beam = (float(beam[0]), float(beam[1]))

        return

    def _help_beam(self):
        '''Return a help string for the read beam method.'''
        return '-beam x,y'

    def getBeam(self):
        return self._beam

    def _help_image(self):
        '''Return a string for explaining the -image method.'''
        return '-image /path/to/an/image_001.img'

    def _read_image(self):
        '''Read image information from the command line.'''

        index = -1

        try:
            index = sys.argv.index('-image')
        except ValueError, e:
            # the token is not on the command line
            self._default_template = None
            self._default_directory = None
            self._default_image = None
            self.write('No image passed in on the command line')
            return

        template, directory = image2template_directory(sys.argv[index + 1])
        self._default_template = template
        self._default_directory = directory
        self._default_image = sys.argv[index + 1]
        return

    def getTemplate(self):
        return self._default_template

    def getDirectory(self):
        return self._default_directory

    def getImage(self):
        return self._default_image

CommandLine = _CommandLine()

if __name__ == '__main__':
    print CommandLine.getBeam()

    
