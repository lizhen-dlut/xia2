from __future__ import absolute_import, division, print_function

import logging
from collections import OrderedDict

import iotbx.phil
from scitbx.array_family import flex
from dials.util import log
from dials.algorithms.symmetry.cosym import plot_dendrogram, plot_matrix

logger = logging.getLogger(__name__)
debug_handle = log.debug_handle(logger)
info_handle = log.info_handle(logger)


def get_scipy():
  # make sure we can get scipy, if not try failing over to version in CCP4
  try:
    import scipy.cluster
    found = True
  except ImportError:
    found = False

  if not found and 'CCP4' in os.environ:
    sys.path.append(os.path.join(os.environ['CCP4'], 'lib', 'python2.7',
                                 'site-packages'))
    try:
      import scipy.cluster
      found = True
    except ImportError:
      found = False

  if not found:
    from libtbx.utils import Sorry
    raise Sorry('%s depends on scipy.cluster, not available' % sys.argv[0])

get_scipy()

batch_phil_scope = """\
batch
  .multiple = True
{
  id = None
    .type = str
  range = None
    .type = ints(size=2, value_min=0)
}
"""

master_phil_scope = iotbx.phil.parse("""\
unit_cell = None
  .type = unit_cell
n_bins = 20
  .type = int(value_min=1)
d_min = None
  .type = float(value_min=0)
%s
""" %batch_phil_scope)


class separate_unmerged(object):

  def __init__(self, unmerged_intensities, batches_all, id_to_batches=None):

    intensities = OrderedDict()
    batches = OrderedDict()

    if id_to_batches is None:
      run_id_to_batch_id = None
      run_id = 0
      unique_batches = sorted(set(batches_all.data()))
      last_batch = None
      run_start = unique_batches[0]
      for i, batch in enumerate(unique_batches):
        if last_batch is not None and batch > (last_batch + 1) or (i+1) == len(unique_batches):
          batch_sel = (batches_all.data() >= run_start) & (batches_all.data() <= last_batch)
          batches[run_id] = batches_all.select(batch_sel)
          intensities[run_id] = unmerged_intensities.select(batch_sel)
          logger.debug("run %i batch %i to %i" %(run_id+1, run_start, last_batch))
          run_id += 1
          run_start = batch
        last_batch = batch

    else:
      run_id_to_batch_id = OrderedDict()
      run_id = 0
      for batch_id, batch_range in id_to_batches.iteritems():
        run_id_to_batch_id[run_id] = batch_id
        run_start, last_batch = batch_range
        batch_sel = (batches_all.data() >= run_start) & (batches_all.data() <= last_batch)
        batches[run_id] = batches_all.select(batch_sel)
        intensities[run_id] = unmerged_intensities.select(batch_sel)
        logger.debug("run %i batch %i to %i" %(run_id+1, run_start, last_batch))
        run_id += 1

    self.run_id_to_batch_id = run_id_to_batch_id
    self.intensities = intensities
    self.batches = batches


class ClusterInfo(object):
  def __init__(self, cluster_id, labels,
               multiplicity, completeness, height=None):
    self.cluster_id = cluster_id
    self.labels = labels
    self.multiplicity = multiplicity
    self.completeness = completeness
    self.height = height

  def __str__(self):
    lines = ['Cluster %i' % self.cluster_id,
             '  Number of datasets: %i' % len(self.labels),
             '  Completeness: %.1f %%' % (self.completeness * 100),
             '  Multiplicity: %.2f' % self.multiplicity,
             '  Datasets:' + ','.join('%s' % s for s in self.labels),
             ]
    if self.height is not None:
      lines.append('  height: %f' % self.height)
    return '\n'.join(lines)


class multi_crystal_analysis(object):

  def __init__(self, unmerged_intensities,
               labels=None,
               prefix=None,
               ):

    self.unmerged_intensities = unmerged_intensities
    self._intensities_all = None
    self._labels_all = flex.size_t()
    if prefix is None:
      prefix = ''
    self._prefix = prefix

    self.intensities = unmerged_intensities
    self.individual_merged_intensities = []
    if labels is None:
      labels = ['%i' %(i+1) for i in range(len(self.intensities))]
    assert len(labels) == len(self.intensities)
    self.labels = labels

    for i, unmerged in enumerate(self.intensities):
      self.individual_merged_intensities.append(
        unmerged.merge_equivalents().array())
      if self._intensities_all is None:
        self._intensities_all = unmerged.deep_copy()
      else:
        self._intensities_all = self._intensities_all.concatenate(unmerged)
      self._labels_all.extend(flex.size_t(unmerged.size(), i))

    self.run_cosym()
    correlation_matrix, linkage_matrix = self.compute_correlation_coefficient_matrix()

    cos_angle_matrix, ca_linkage_matrix = self.compute_cos_angle_matrix()

    plot_matrix(correlation_matrix.as_numpy_array(), linkage_matrix,
                file_name='%scc_matrix.png' % self._prefix,
                labels=labels)

    plot_dendrogram(linkage_matrix,
                    file_name='%scc_dendrogram.png' % self._prefix,
                    labels=labels)

    d = self.to_plotly_json(
      correlation_matrix, linkage_matrix, labels=labels)

    import json
    with open('%sintensity_clusters.json' % self._prefix, 'wb') as f:
      json.dump(d, f, indent=2)

    plot_matrix(cos_angle_matrix.as_numpy_array(), ca_linkage_matrix,
                file_name='%scos_angle_matrix.png' % self._prefix,
                labels=labels)

    plot_dendrogram(ca_linkage_matrix,
                    file_name='%scos_angle_dendrogram.png' % self._prefix,
                    labels=labels)

    d = self.to_plotly_json(
      cos_angle_matrix, ca_linkage_matrix, labels=labels)

    import json
    with open('%scos_angle_clusters.json' % self._prefix, 'wb') as f:
      json.dump(d, f, indent=2)

    self.cos_angle_linkage_matrix = ca_linkage_matrix
    self.cos_angle_matrix = cos_angle_matrix
    self.cos_angle_clusters = self.cluster_info(
      self.linkage_matrix_to_dict(self.cos_angle_linkage_matrix))
    self.cc_linkage_matrix = linkage_matrix
    self.cc_matrix = correlation_matrix
    self.cc_clusters = self.cluster_info(
      self.linkage_matrix_to_dict(self.cc_linkage_matrix))

    logger.info('\nIntensity correlation clustering summary:')
    logger.info(self.as_table(self.cc_clusters))

    logger.info('\nCos(angle) clustering summary:')
    logger.info(self.as_table(self.cos_angle_clusters))

  def cluster_info(self, cluster_dict):
    info = []
    for cluster_id, cluster in cluster_dict.iteritems():
      sel_cluster = flex.bool(self._labels_all.size(), False)
      for j in cluster['datasets']:
        sel_cluster |= (self._labels_all == j)
      intensities_cluster = self._intensities_all.select(sel_cluster)
      merging = intensities_cluster.merge_equivalents()
      merged_intensities = merging.array()
      multiplicities = merging.redundancies()
      dataset_ids = cluster['datasets']
      labels = [self.labels[i-1] for i in dataset_ids]
      info.append(ClusterInfo(
        cluster_id, labels,
        flex.mean(multiplicities.data().as_double()),
        merged_intensities.completeness(),
        height=cluster.get('height')
      ))
    return info

  def as_table(self, cluster_info):
    from libtbx.str_utils import wordwrap
    rows = []
    headers = ['Cluster', 'Datasets', 'Height', 'Multiplicity', 'Completeness']
    for info in cluster_info:
      rows.append(
        ['%i' % info.cluster_id,
         wordwrap(' '.join('%s' % l for l in info.labels)),
         '%.2g' % info.height,
         '%.1f' % info.multiplicity,
         '%.2f' % info.completeness,
         ]
      )

    # sort table by completeness
    perm = flex.sort_permutation(
      flex.double(c.completeness for c in cluster_info))
    rows = [rows[i] for i in perm]

    import tabulate
    return tabulate.tabulate(rows, headers, tablefmt='rst')

  @staticmethod
  def linkage_matrix_to_dict(linkage_matrix):

    from scipy.cluster import hierarchy
    tree = hierarchy.to_tree(linkage_matrix, rd=False)
    leaves_list = hierarchy.leaves_list(linkage_matrix)

    d = {}

    # http://w3facility.org/question/scipy-dendrogram-to-json-for-d3-js-tree-visualisation/
    # https://gist.github.com/mdml/7537455

    def add_node(node):
      if node.is_leaf(): return
      cluster_id = node.get_id() - len(linkage_matrix) - 1
      row = linkage_matrix[cluster_id]
      d[cluster_id+1] = {
        'datasets': [i+1 for i in sorted(node.pre_order())],
        'height': row[2],
      }

      # Recursively add the current node's children
      if node.left: add_node(node.left)
      if node.right: add_node(node.right)

    add_node(tree)

    return d

  def run_cosym(self):
    from dials.algorithms.symmetry.cosym import phil_scope
    params = phil_scope.extract()
    from dials.algorithms.symmetry.cosym import analyse_datasets
    datasets = self.individual_merged_intensities
    datasets = [d.primitive_setting() for d in datasets]
    params.lattice_group = datasets[0].space_group_info()
    params.cluster.method = "dbscan"
    params.plot_prefix = self._prefix

    results = analyse_datasets(self.individual_merged_intensities, params)
    results.plot()
    self.cosym = results

  def compute_correlation_coefficient_matrix(self):
    from scipy.cluster import hierarchy
    import scipy.spatial.distance as ssd

    correlation_matrix = self.cosym.target.rij_matrix

    for i in range(correlation_matrix.all()[0]):
      correlation_matrix[i, i] = 1

    # clip values of correlation matrix to account for floating point errors
    correlation_matrix.set_selected(correlation_matrix < -1, -1)
    correlation_matrix.set_selected(correlation_matrix > 1, 1)
    diffraction_dissimilarity = 1-correlation_matrix

    dist_mat = diffraction_dissimilarity.as_numpy_array()

    # convert the redundant n*n square matrix form into a condensed nC2 array
    dist_mat = ssd.squareform(dist_mat) # distArray[{n choose 2}-{n-i choose 2} + (j-i-1)] is the distance between points i and j

    linkage_matrix = hierarchy.linkage(dist_mat, method='average')

    return correlation_matrix, linkage_matrix

  def compute_cos_angle_matrix(self):
    from scipy.cluster import hierarchy
    import scipy.spatial.distance as ssd
    dist_mat = ssd.pdist(self.cosym.coords.as_numpy_array(), metric='cosine')
    cos_angle = 1 - ssd.squareform(dist_mat)
    linkage_matrix = hierarchy.linkage(dist_mat, method='average')
    return flex.double(cos_angle), linkage_matrix

  @staticmethod
  def to_plotly_json(correlation_matrix,
                     linkage_matrix, labels=None):

    from scipy.cluster import hierarchy
    ddict = hierarchy.dendrogram(linkage_matrix,
                                 color_threshold=0.05,
                                 labels=labels,
                                 show_leaf_counts=False)

    import copy
    y2_dict = scipy_dendrogram_to_plotly_json(ddict) # above heatmap
    x2_dict = copy.deepcopy(y2_dict) # left of heatmap, rotated
    for d in y2_dict['data']:
      d['yaxis'] = 'y2'
      d['xaxis'] = 'x2'

    for d in x2_dict['data']:
      x = d['x']
      y = d['y']
      d['x'] = y
      d['y'] = x
      d['yaxis'] = 'y3'
      d['xaxis'] = 'x3'

    D = correlation_matrix.as_numpy_array()
    ccdict = {
      'data': [{
        'name': 'correlation_matrix',
        'x': list(range(D.shape[0])),
        'y': list(range(D.shape[1])),
        'z': D.tolist(),
        'type': 'heatmap',
        'colorbar': {
          'title': 'Correlation coefficient',
          'titleside': 'right',
          'xpad': 0,
        },
        'colorscale': 'Jet',
        'xaxis': 'x',
        'yaxis': 'y',
      }],

      'layout': {
        'autosize': False,
        'bargap': 0,
        'height': 1000,
        'hovermode': 'closest',
        'margin': {
          'r': 20,
          't': 50,
          'autoexpand': True,
          'l': 20
          },
        'showlegend': False,
        'title': 'Dendrogram Heatmap',
        'width': 1000,
        'xaxis': {
          'domain': [0.2, 0.9],
          'mirror': 'allticks',
          'showgrid': False,
          'showline': False,
          'showticklabels': True,
          'tickmode': 'array',
          'ticks': '',
          'ticktext': y2_dict['layout']['xaxis']['ticktext'],
          'tickvals': list(range(len(y2_dict['layout']['xaxis']['ticktext']))),
          'tickangle': 300,
          'title': '',
          'type': 'linear',
          'zeroline': False
        },
        'yaxis': {
          'domain': [0, 0.78],
          'anchor': 'x',
          'mirror': 'allticks',
          'showgrid': False,
          'showline': False,
          'showticklabels': True,
          'tickmode': 'array',
          'ticks': '',
          'ticktext': y2_dict['layout']['xaxis']['ticktext'],
          'tickvals': list(range(len(y2_dict['layout']['xaxis']['ticktext']))),
          'title': '',
          'type': 'linear',
          'zeroline': False
        },
        'xaxis2': {
          'domain': [0.2, 0.9],
          'anchor': 'y2',
          'showgrid': False,
          'showline': False,
          'showticklabels': False,
          'zeroline': False
        },
        'yaxis2': {
          'domain': [0.8, 1],
          'anchor': 'x2',
          'showgrid': False,
          'showline': False,
          'zeroline': False
        },
        'xaxis3': {
          'domain': [0.0, 0.1],
          'anchor': 'y3',
          'range': [max(max(d['x']) for d in x2_dict['data']), 0],
          'showgrid': False,
          'showline': False,
          'tickangle': 300,
          'zeroline': False
        },
        'yaxis3': {
          'domain': [0, 0.78],
          'anchor': 'x3',
          'showgrid': False,
          'showline': False,
          'showticklabels': False,
          'zeroline': False
        },
      }
    }
    d = ccdict
    d['data'].extend(y2_dict['data'])
    d['data'].extend(x2_dict['data'])

    d['clusters'] = multi_crystal_analysis.linkage_matrix_to_dict(linkage_matrix)

    return d


def scipy_dendrogram_to_plotly_json(ddict):
  colors = { 'b': 'rgb(31, 119, 180)',
             'g': 'rgb(44, 160, 44)',
             'o': 'rgb(255, 127, 14)',
             'r': 'rgb(214, 39, 40)',
  }

  dcoord = ddict['dcoord']
  icoord = ddict['icoord']
  color_list = ddict['color_list']
  ivl = ddict['ivl']
  leaves = ddict['leaves']

  data = []
  xticktext = []
  xtickvals = []

  for k in range(len(dcoord)):
    x = icoord[k]
    y = dcoord[k]

    if y[0] == 0:
      xtickvals.append(x[0])
    if y[3] == 0:
      xtickvals.append(x[3])

    data.append({
      'x': x,
      'y': y,
      'marker': {
        'color': colors.get(color_list[k]),
      },
      'mode':"lines",
    })

  xtickvals = sorted(xtickvals)
  xticktext = ivl
  d = {
    'data': data,
    'layout': {
      'barmode': 'group',
      'legend': {
        'x': 100,
        'y': 0.5,
        'bordercolor': 'transparent'
      },
      'margin': {
        'r': 10
      },
      'showlegend': False,
      'title': 'BLEND dendrogram',
      'xaxis': {
        'showline': False,
        'showgrid': False,
        'showticklabels': True,
        'tickangle': 300,
        'title': 'Individual datasets',
        'titlefont': {
          'color': 'none'
        },
        'type': 'linear',
        'ticktext': xticktext,
        'tickvals': xtickvals,
        'tickorientation': 'vertical',
      },
      'yaxis': {
        'showline': False,
        'showgrid': False,
        'showticklabels': True,
        'tickangle': 0,
        'title': 'Ward distance',
        'type': 'linear'
      },
      'hovermode': 'closest',
    }
  }
  return d
