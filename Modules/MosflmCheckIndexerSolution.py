#!/usr/bin/env python
# MosflmCheckIndexerSolution.py
#   Copyright (C) 2009 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is 
#   included in the root directory of this package.
# 12th May 2009
# 
# Code to check the autoindex solution from mosflm for being
# pseudo-centred (i.e. comes out as centered when it should not be)
#

import os
import math
import sys

if not os.environ.has_key('XIA2_ROOT'):
    raise RuntimeError, 'XIA2_ROOT not defined'

if not os.environ['XIA2_ROOT'] in sys.path:
    sys.path.append(os.environ['XIA2_ROOT'])

# xia2 stuff...

from Wrappers.XIA.Printpeaks import Printpeaks
from Wrappers.XIA.Diffdump import Diffdump
from Handlers.Streams import Debug
from lib.Guff import nint
from Experts.MatrixExpert import format_matrix

# cctbx stuff

from cctbx import sgtbx
from cctbx import crystal
from cctbx import uctbx
from scitbx import matrix

def s2l(spacegroup):
    lattice_to_spacegroup = {'aP':1, 'mP':3, 'mC':5, 
                             'oP':16, 'oC':20, 'oF':22,
                             'oI':23, 'tP':75, 'tI':79,
                             'hP':143, 'hR':146, 'cP':195,
                             'cF':196, 'cI':197}

    spacegroup_to_lattice = { }
    for k in lattice_to_spacegroup.keys():
        spacegroup_to_lattice[lattice_to_spacegroup[k]] = k
    return spacegroup_to_lattice[spacegroup]

def l2s(lattice):
    lattice_to_spacegroup = {'aP':1, 'mP':3, 'mC':5, 
                             'oP':16, 'oC':20, 'oF':22,
                             'oI':23, 'tP':75, 'tI':79,
                             'hP':143, 'hR':146, 'cP':195,
                             'cF':196, 'cI':197}
    return lattice_to_spacegroup[lattice]

def mosflm_check_indexer_solution(indexer):

    distance = indexer.get_indexer_distance()
    axis = matrix.col([0, 0, 1])
    beam = indexer.get_indexer_beam()
    cell = indexer.get_indexer_cell()
    wavelength = indexer.get_wavelength()

    space_group_number = l2s(indexer.get_indexer_lattice())
    spacegroup = sgtbx.space_group_symbols(space_group_number).hall()
    phi = indexer.get_header()['phi_width']

    sg = sgtbx.space_group(spacegroup)

    if not (sg.n_ltr() - 1):
        # primitive solution - just return ... something
        return None, None, None, None

    # FIXME need to raise an exception if this is not available!
    m_matrix = indexer.get_indexer_payload('mosflm_orientation_matrix')

    # N.B. in the calculation below I am using the Cambridge frame
    # and Mosflm definitions of X & Y...
    
    m_elems = []
    
    for record in m_matrix[:3]:
        record = record.replace('-', ' -')
        for e in map(float, record.split()):
            m_elems.append(e / wavelength)

    mi = matrix.sqr(m_elems)
    m = mi.inverse()
    
    A = matrix.col(m.elems[0:3])
    B = matrix.col(m.elems[3:6])
    C = matrix.col(m.elems[6:9])

    # now select the images - start with the images that the indexer
    # used for indexing, though can interrogate the FrameProcessor
    # interface of the indexer to put together a completely different
    # list if I like...
    
    images = []

    for i in indexer.get_indexer_images():
        for j in i:
            if not j in images:
                images.append(j)

    images.sort()

    if False:

        all_images = indexer.get_matching_images()
        
        images = [min(all_images)]
        step = nint(5.0 / phi)
        next = images[0] + step
        
        while next in all_images:
            images.append(next)
            next += step

    # now construct the reciprocal-space peak list n.b. should
    # really run this in parallel...

    spots_r = []
    
    for i in images:
        image = indexer.get_image_name(i)
        dd = Diffdump()
        dd.set_image(image)
        header = dd.readheader()
        phi = header['phi_start'] + 0.5 * header['phi_width']
        pixel = header['pixel']
        wavelength = header['wavelength']
        pp = Printpeaks()
        pp.set_image(image)
        peaks = pp.get_maxima()

        for p in peaks:
            x, y, isigma = p

            if isigma < 5.0:
                continue

            xp = pixel[0] * y - beam[0]
            yp = pixel[1] * x - beam[1]

            scale = wavelength * math.sqrt(
                xp * xp + yp * yp + distance * distance)

            X = distance / scale
            X -= 1.0 / wavelength
            Y = - xp / scale
            Z = yp / scale

            S = matrix.col([X, Y, Z])

            rtod = 180.0 / math.pi

            spots_r.append(S.rotate(axis, - phi / rtod))
            
    # now reindex the reciprocal space spot list and count - n.b. need
    # to transform the Bravais lattice to an assumed spacegroup and hence
    # to a cctbx spacegroup!

    absent = 0
    present = 0
    total = 0

    for spot in spots_r:
        hkl = (m * spot).elems

        total += 1

        ihkl = map(nint, hkl)

        # print '%6.2f %6.2f %6.2f' % tuple(hkl), '%3d %3d %3d' % tuple(ihkl)

        if math.fabs(hkl[0] - ihkl[0]) > 0.1:
            continue

        if math.fabs(hkl[1] - ihkl[1]) > 0.1:
            continue
        
        if math.fabs(hkl[2] - ihkl[2]) > 0.1:
            continue

        # now determine if it is absent

        if sg.is_sys_absent(ihkl):
            absent += 1
        else:
            present += 1

    # now perform the analysis on these numbers...

    sd = math.sqrt(absent)

    print total, present, absent, (absent - 3 * sd) / total

    if (absent - 3 * sd) / total < 0.008:
        return False, None, None, None

    # in here need to calcuylate the new orientation matrix for the
    # primitive basis and reconfigure the indexer - somehow...

    # ok, so the bases are fine, but what I will want to do is reorder them
    # to give the best primitive choice of unit cell...

    sgp = sg.build_derived_group(True, False)
    lattice_p = s2l(sgp.type().number())
    symm = crystal.symmetry(unit_cell = cell,
                            space_group = sgp)

    rdx = symm.change_of_basis_op_to_best_cell()
    symm_new = symm.change_basis(rdx)

    # now apply this to the reciprocal-space orientation matrix mi

    # cb_op = sgtbx.change_of_basis_op(rdx)
    cb_op = rdx
    R = cb_op.c_inv().r().as_rational().as_float().transpose().inverse()
    mi_r = mi * R

    # now re-derive the cell constants, just to be sure

    m_r = mi_r.inverse()
    Ar = matrix.col(m_r.elems[0:3])
    Br = matrix.col(m_r.elems[3:6])
    Cr = matrix.col(m_r.elems[6:9])

    a = math.sqrt(Ar.dot())
    b = math.sqrt(Br.dot())
    c = math.sqrt(Cr.dot())

    rtod = 180.0 / math.pi

    alpha = rtod * Br.angle(Cr)
    beta = rtod * Cr.angle(Ar)
    gamma = rtod * Ar.angle(Br)

    print '%6.3f %6.3f %6.3f %6.3f %6.3f %6.3f' % (a, b, c, alpha, beta, gamma)

    cell = uctbx.unit_cell((a, b, c, alpha, beta, gamma))

    bmat = matrix.sqr(cell.fractionalization_matrix())
    umat = mi_r * bmat.inverse()

    new_matrix = format_matrix((a, b, c, alpha, beta, gamma),
                               mi_r.elems, umat.elems)

    # ok - this gives back the right matrix in the right setting - excellent!
    # now need to apply this back at base to the results of the indexer.

    # N.B. same should be applied to the same calculations for the XDS
    # version of this.

    return True, lattice_p, new_matrix, (a, b, c, alpha, beta, gamma)
        
if __name__ == '__main__':

    # run a test!

    from Modules.IndexerFactory import Indexer

    i = Indexer()
    
    i.setup_from_image(sys.argv[1])

    print 'Refined beam is: %6.2f %6.2f' % i.get_indexer_beam()
    print 'Distance:        %6.2f' % i.get_indexer_distance()
    print 'Cell: %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f' % i.get_indexer_cell()
    print 'Lattice: %s' % i.get_indexer_lattice()
    print 'Mosaic: %6.2f' % i.get_indexer_mosaic()
    
    status = mosflm_check_indexer_solution(i)

    if status is True:
        print 'putative centred solution came out as wrong'

    elif status is False:
        print 'putative centred solution came out as right'

    elif status is None:
        print 'putative solution not centred'
