#!/usr/bin/env python
# Environment.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# Maintained by Graeme Winter
# 18th September 2006
#
# A handler for matters of the operating environment, which will impact
# on data harvesting, working directories, a couple of other odds & sods.
#
#
#

import os
import sys
import subprocess
import stat
import platform
import ctypes
import tempfile

if not os.environ.has_key('XIA2_ROOT'):
    raise RuntimeError, 'XIA2_ROOT not defined'
if not os.environ['XIA2_ROOT'] in sys.path:
    sys.path.append(os.path.join(os.environ['XIA2_ROOT']))

from Handlers.Streams import Chatter, Debug

def df(path = os.getcwd()):
    '''Return disk space in bytes in path.'''

    if platform.system() == 'Windows':
        bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(path), None, None, ctypes.pointer(bytes))
        return bytes.value
    else:
        s = os.statvfs(path)
        return s.f_frsize * s.f_bavail

    raise RuntimeError, 'platform not supported'

class _Environment:
    '''A class to store environmental considerations.'''

    def __init__(self):
        self._cwd = os.getcwd()
        self._is_setup = False
        # self._setup()
        return

    def _setup(self):
        if self._is_setup:
            return

        self._is_setup = True
        harvest_directory = self.generate_directory('Harvest')
        self.setenv('HARVESTHOME', harvest_directory)

        # create a USER environment variable, to allow harvesting
        # in Mosflm to work (hacky, I know, but it really doesn't
        # matter too much...
        if not os.environ.has_key('USER'):
            os.environ['USER'] = 'xia2'

        # create a random BINSORT_SCR directory, check how much space we
        # have in there...

        binsort_scr = tempfile.mkdtemp()
        os.environ['BINSORT_SCR'] = binsort_scr
        Debug.write('Created BINSORT_SCR: %s' % binsort_scr)

        try:
            space = df(binsort_scr) / (1024.0 * 1024.0)
            Debug.write('Space in BINSORT_SCR: %.2f GB' % (space / 1024.0))
            if space < 200.0:
                Chatter.write('Warning: < 200MB in BINSORT_SCR')
                
        except RuntimeError, e:
            pass
            
        self._is_setup = True

        return

    def generate_directory(self, path_tuple):
        '''Used for generating working directories.'''
        self._setup()

        path = self._cwd

        if type(path_tuple) == type('string'):
            path_tuple = (path_tuple,)

        for p in path_tuple:
            path = os.path.join(path, p)

        if not os.path.exists(path):
            Debug.write('Making directory: %s' % path)
            os.makedirs(path)
        else:
            Debug.write('Directory exists: %s' % path)

        return path

    def setenv(self, name, value):
        '''A wrapper for os.environ.'''

        self._setup()
        os.environ[name] = value

        return

    def getenv(self, name):
        '''A wrapper for os.environ.'''
        self._setup()
        return os.environ.get(name, None)

    def cleanup(self):
        '''Clean up now we are done - chown all harvest files to world
        readable.'''

        if not self._is_setup:
            return

        if os.name != 'posix':
            return

        harvest = self.getenv('HARVESTHOME')

        mod = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH

        for (dirpath, dirnames, filenames) in os.walk(harvest):

            for f in filenames:
                _f = os.path.join(harvest, dirpath, f)
                os.chmod(_f, mod)

        return

Environment = _Environment()

# jiffy functions

def get_number_cpus():
    '''Portably get the number of processor cores available.'''

    # Windows NT derived platforms

    if os.name == 'nt':
        return int(os.environ['NUMBER_OF_PROCESSORS'])

    # linux

    if os.path.exists('/proc/cpuinfo'):
        n_cpu = 0

        for record in open('/proc/cpuinfo', 'r').readlines():
            if not record.strip():
                continue
            if 'processor' in record.split()[0]:
                n_cpu += 1

        return n_cpu

    # os X

    output = subprocess.Popen(['system_profiler', 'SPHardwareDataType'],
                              stdout = subprocess.PIPE).communicate()[0]

    ht = 1

    for record in output.split('\n'):
        if 'Intel Core i7' in record:
            ht = 2
        if 'Total Number Of Cores' in record:
            return ht * int(record.split()[-1])
        if 'Total Number of Cores' in record:
            return ht * int(record.split()[-1])

    return -1

if __name__ == '__main__':

    print get_number_cpus()
    print df(os.getcwd())
