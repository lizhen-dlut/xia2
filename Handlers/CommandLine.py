#!/usr/bin/env python
# CommandLine.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the terms and conditions of the
#   CCP4 Program Suite Licence Agreement as a CCP4 Library.
#   A copy of the CCP4 licence can be obtained by writing to the
#   CCP4 Secretary, Daresbury Laboratory, Warrington WA4 4AD, UK.
#
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
# 16/AUG/06 - FIXME - need to be able to handle a resolution limit in here 
#             as well as any other information our user may wish to pass
#             in on the comand line, for example a lattice or a spacegroup.
# 
# 23/AUG/06 - FIXME - need to add handling of the lattice input in particular,
#             since this is directly supported by Mosflm.py...
#
# 04/SEP/06 - FIXME - need to be able to pass in a resolution limit to
#             work to, for development purposes (this should become
#             automatic in the future.)

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

        try:
            self._read_lattice_spacegroup()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_lattice_spacegroup(), str(e))

        try:
            self._read_resolution_limit()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_resolution_limit(), str(e))

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

        image = sys.argv[index + 1]

        # check if there is a space in the image name - this happens and it
        # looks like the python input parser will split it even if the
        # space is escaped or it is quoted

        if image[-1] == '\\':
            try:
                image = '%s %s' % (sys.argv[index + 1][:-1],
                                   sys.argv[index + 2])
            except:
                raise RuntimeError, 'image name ends in \\'

        template, directory = image2template_directory(image)
        self._default_template = template
        self._default_directory = directory
        self._default_image = image
        return

    def _read_lattice_spacegroup(self):
        '''Check for -lattice or -spacegroup tokens on the command
        line.'''

        # have to enforce not making both selections...

        index_lattice = -1
        index_spacegroup = -1

        try:
            index_lattice = sys.argv.index('-lattice')

            # FIXME need to check that this token exists on the
            # command line and that the value is a meaningful
            # crystallographic lattice...
            
            self._default_lattice = sys.argv[index_lattice + 1]

        except ValueError, e:
            # this token is not on the command line
            self._default_lattice = None

        # FIXME need to check for the spacegroup and do something
        # sensible with it... but this will require implementing
        # this for all of the interfaces, which is not yet done...

        return

    def _help_lattice_spacegroup(self):
        '''Help for the lattice/spacegroup options.'''
        return '(-lattice mP|-spacegroup p2)'

    def _read_resolution_limit(self):
        '''Search for resolution limit on the command line - at the
        moment just the high resolution limit.'''

        try:
            index = sys.argv.index('-resolution')

        except ValueError, e:
            self._default_resolution_limit = 0.0
            return

        self._default_resolution_limit = float(sys.argv[index + 1])
        
        return

    def _help_resolution_limit(self):
        return '-resolution 1.6'
    
    def getTemplate(self):
        return self._default_template

    def getDirectory(self):
        return self._default_directory

    def getImage(self):
        return self._default_image

    def getLattice(self):
        return self._default_lattice

    def getSpacegroup(self):
        raise RuntimeError, 'this needs to be implemented'

    def getResolution_limit(self):
        return self._default_resolution_limit

CommandLine = _CommandLine()

if __name__ == '__main__':
    print CommandLine.getBeam()
    print CommandLine.getResolution_limit()

