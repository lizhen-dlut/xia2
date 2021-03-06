#!/usr/bin/env python
# StereographicProjection.py
#
#   Copyright (C) 2017 Diamond Light Source, Richard Gildea
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#

from __future__ import absolute_import, division, print_function

def StereographicProjection(DriverType = None):
  '''A factory for StereographicProjectionWrapper classes.'''

  from xia2.Driver.DriverFactory import DriverFactory
  DriverInstance = DriverFactory.Driver(DriverType)

  class StereographicProjectionWrapper(DriverInstance.__class__):

    def __init__(self):
      DriverInstance.__class__.__init__(self)

      self.set_executable('dials.stereographic_projection')

      self._experiments_filenames = []
      self._hkl = None
      self._plot_filename = None
      self._json_filename = None

    def add_experiments(self, experiments_filename):
      self._experiments_filenames.append(experiments_filename)

    def set_hkl(self, hkl):
      assert len(hkl) == 3
      self._hkl = hkl

    def get_plot_filename(self):
      return self._plot_filename

    def get_json_filename(self):
      return self._json_filename

    def run(self):
      from xia2.Handlers.Streams import Debug
      Debug.write('Running dials.stereographic_projection')

      assert len(self._experiments_filenames) > 0
      assert self._hkl is not None

      self.clear_command_line()
      for expt in self._experiments_filenames:
        self.add_command_line(expt)
      self.add_command_line('frame=laboratory')
      self.add_command_line('plot.show=False')
      self.add_command_line('hkl=%i,%i,%i' %self._hkl)
      self._plot_filename = '%i_stereographic_projection_%i%i%i.png' % (
        self.get_xpid(), self._hkl[0], self._hkl[1], self._hkl[2])
      self._json_filename = '%i_stereographic_projection_%i%i%i.json' % (
        self.get_xpid(), self._hkl[0], self._hkl[1], self._hkl[2])
      self.add_command_line('plot.filename=%s' %self._plot_filename)
      self.add_command_line('json.filename=%s' %self._json_filename)

      self.start()
      self.close_wait()
      self.check_for_errors()

  return StereographicProjectionWrapper()
