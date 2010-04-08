#!/usr/bin/env python
# NullIntegrater.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is 
#   included in the root directory of this package.
#
# 30/OCT/06
#
# An empty integrater - this presents the Integrater interface but does 
# nothing, making it ideal for when you have the integrated intensities
# passed in already. This will simply return the intensities.
#
# FIXME 08/NOV/06 need to be able to limit in both batches and in resolution.
#                 Therefore need to also include the Rebatch wrapper...
# 

import os
import sys

if not os.environ.has_key('XIA2_ROOT'):
    raise RuntimeError, 'XIA2_ROOT not defined'

if not os.environ['XIA2_ROOT'] in sys.path:
    sys.path.append(os.environ['XIA2_ROOT'])

from Schema.Interfaces.Integrater import Integrater
from Schema.Interfaces.FrameProcessor import FrameProcessor
from Wrappers.CCP4.Mtzutils import Mtzutils
from Wrappers.CCP4.Mtzdump import Mtzdump
from Wrappers.CCP4.Reindex import Reindex

from Handlers.Streams import Chatter
from Handlers.Syminfo import Syminfo

from lib.Guff import auto_logfiler
from lib.SymmetryLib import lattice_to_spacegroup

class NullIntegrater(FrameProcessor,
                     Integrater):
    '''A null class to present the integrater interface.'''

    def __init__(self, integrated_reflection_file):
        '''Create a null integrater pointing at this reflection file.'''

        FrameProcessor.__init__(self)
        Integrater.__init__(self)

        self._intgr_hklout_orig = integrated_reflection_file
        self._intgr_hklout = None

        self._working_directory = os.getcwd()

        # also need to be able to set the epoch of myself
        # FIXME - this is also generally true... need to add
        # this to the .xinfo file...

        self._null_integrater_spacegroup = None
        self._null_integrater_hklout = None

        return

    def set_working_directory(self, working_directory):
        self._working_directory = working_directory
        pass

    def get_working_directory(self):
        return self._working_directory

    # overload these methods from the interface to provide a workaround
    def get_integrater_prepare_done(self):
        return self._intgr_prepare_done

    def get_integrater_done(self):
        return self._intgr_done    

    # "real" methods

    def _integrate_prepare(self):
        '''Learn about the reflection file.'''

        md = Mtzdump()

        md.set_working_directory(self.get_working_directory())
        auto_logfiler(md)
        md.set_hklin(self._intgr_hklout_orig)
        
        md.dump()
        datasets = md.get_datasets()
    
        for d in datasets:
            info = md.get_dataset_info(d)
            spacegroup = Syminfo.spacegroup_name_to_number(
                info['spacegroup'])
            if self._null_integrater_spacegroup is None:
                self._null_integrater_spacegroup = spacegroup
            else:
                if self._null_integrater_spacegroup != spacegroup:
                    raise RuntimeError, 'null integrater spacegroup error'

    def _integrate(self):
        '''Do nothing - except return a pointer to the reflections...'''

        # FIXME 08/NUV/06 this should probably return a reflection file
        # which has been resolution limited appropriately...

        # run Mtzutils if we have defined a resolution limit, else just
        # return a pointer to the original reflection file...

        if not self._intgr_reso_high:
            self._intgr_hklout = self._intgr_hklout_orig
            
        else:
            # construct a name for hklout...
            hklout = os.path.join(self.get_working_directory(),
                                  os.path.split(self._intgr_hklout_orig)[-1])

            if hklout == self._intgr_hklout_orig:
                raise RuntimeError, 'cannot have input reflections in ' + \
                      'working directory'
            
            # run mtzutils

            mu = Mtzutils()

            mu.set_working_directory(self.get_working_directory())

            auto_logfiler(mu)

            Chatter.write('NULL integrater resolution limited to %5.2f' %
                          self._intgr_reso_high)
            Chatter.write('=> %s' % hklout)

            mu.set_hklin(self._intgr_hklout_orig)
            mu.set_hklout(hklout)
            mu.set_resolution(self._intgr_reso_high)

            mu.edit()

            self._intgr_hklout = hklout
            
        self._null_integrater_hklout = self._intgr_hklout

        return self._intgr_hklout

    def _integrate_finish(self):
        '''Finish the integration - if necessary performing reindexing
        based on the pointgroup and the reindexing operator.'''
        
        # check if we need to perform any reindexing...

        if not self._intgr_spacegroup_number and \
           not self._intgr_reindex_operator:
            return self._intgr_hklout
        
        Chatter.write('Reindexing to spacegroup %d (%s)' % \
                      (self._intgr_spacegroup_number,
                       self._intgr_reindex_operator))

        hklin = self._null_integrater_hklout
        reindex = Reindex()
        reindex.set_working_directory(self.get_working_directory())
        auto_logfiler(reindex)
        
        reindex.set_operator(self._intgr_reindex_operator)
        
        if self._intgr_spacegroup_number:
            reindex.set_spacegroup(self._intgr_spacegroup_number)
            
        hklout = '%s_reindex.mtz' % hklin[:-4]

        reindex.set_hklin(hklin)
        reindex.set_hklout(hklout)
        
        reindex.reindex()
        
        self._intgr_hklout = hklout
        return hklout


    