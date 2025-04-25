## START OF MODULE


## ###############################################################
## DEPENDANCIES
## ###############################################################
import numpy
from jormi.ww_data import smooth_data


## ###############################################################
## FUNCTIONS
## ###############################################################
def compute_p_norm(
    array_a             : numpy.ndarray,
    array_b             : numpy.ndarray,
    p_norm_order        : float = 2,
    normalise_by_length : bool = False,
  ) -> float:
  """Compute the p-norm between two arrays and optionally normalise by num_points^(1/p_norm_order)."""
  array_a = numpy.asarray(array_a)
  array_b = numpy.asarray(array_b)
  errors = []
  if array_a.ndim != 1: errors.append(f"Array-A must be 1-dimensional, but ndim = {array_a.ndim}.")
  if array_b.ndim != 1: errors.append(f"Array-B must be 1-dimensional, but ndim = {array_b.ndim}.")
  if len(array_a) != len(array_b): errors.append(f"Both arrays must have the same number of elems: {len(array_a)} != {len(array_b)}.")
  if array_a.size == 0: errors.append("Array-A should not be empty.")
  if array_b.size == 0: errors.append("Array-B should not be empty.")
  if not isinstance(p_norm_order, (int, float)): errors.append(f"Invalid norm order `p_norm_order = {p_norm_order}`. Must be a number.")
  if len(errors) > 0: raise ValueError("Input validation failed with the following issues:\n" + "\n".join(errors))
  if numpy.all(array_a == array_b): return 0
  array_diff = numpy.abs(array_a - array_b)
  if p_norm_order == numpy.inf: return numpy.max(array_diff)
  elif p_norm_order == 1:
    ## L1 norm: sum of absolute differences
    value = numpy.sum(array_diff)
    if normalise_by_length: value /= len(array_a)
  elif p_norm_order == 0:
    ## L0 pseudo-norm: count of non-zero elements
    value = numpy.count_nonzero(array_diff)
  elif p_norm_order > 0:
    ## general case for p_norm_order > 0
    ## note improved numerical stability: scale by maximum value
    max_diff = numpy.max(array_diff)
    if max_diff > 0:
        scaled_diff = array_diff / max_diff
        value = max_diff * numpy.power(numpy.sum(numpy.power(scaled_diff, p_norm_order)), 1/p_norm_order)
        if normalise_by_length: value /= numpy.power(len(array_a), 1/p_norm_order)
    else: value = 0
  else: raise ValueError(f"Invalid norm order `p_norm_order = {p_norm_order}`. Must be positive or infinity.")
  return value

def sample_gaussian_distribution_from_quantiles(q1, q2, p1, p2, num_samples=10**3):
  """Sample a normal distribution with quantiles 0 < q1 < q2 < 100 and corresponding probabilities 0 < p1 < p2 < 1."""
  if not (0 < q1 < q2 < 1): raise ValueError("Invalid quantile probabilities")
  ## calculate the inverse of the CDF
  cdf_inv_p1 = numpy.sqrt(2) * numpy.erfinv(2 * q1 - 1)
  cdf_inv_p2 = numpy.sqrt(2) * numpy.erfinv(2 * q2 - 1)
  ## calculate the mean and standard deviation of the normal distribution
  mean_value = ((p1 * cdf_inv_p2) - (p2 * cdf_inv_p1)) / (cdf_inv_p2 - cdf_inv_p1)
  std_value = (p2 - p1) / (cdf_inv_p2 - cdf_inv_p1)
  ## generate sampled points from the normal distribution
  samples = mean_value + std_value * numpy.random.randn(num_samples)
  return samples

def estimate_jpdf(
    data_x            : numpy.ndarray,
    data_y            : numpy.ndarray,
    data_weights      : numpy.ndarray | None = None,
    bin_centers_cols  : numpy.ndarray | None = None,
    bin_centers_rows  : numpy.ndarray | None = None,
    num_bins          : int | None = None,
    bin_range_percent : float = 1.0,
    smoothing_length  : float | None = None,
  ):
  """Compute the 2D joint probability density function (JPDF)."""
  if (len(data_x) == 0) or (len(data_y) == 0):
    raise ValueError("Data arrays must not be empty.")
  if (bin_centers_cols is None) and (bin_centers_rows is None) and (num_bins is None):
    raise ValueError("You did not provide a binning option.")
  if num_bins is None:
    if bin_centers_cols is not None: num_bins = len(bin_centers_cols)
    if bin_centers_rows is not None: num_bins = len(bin_centers_rows)
  if bin_centers_cols is None: bin_centers_cols = create_uniformly_spaced_bin_centers(data_x, num_bins, bin_range_percent)
  if bin_centers_rows is None: bin_centers_rows = create_uniformly_spaced_bin_centers(data_y, num_bins, bin_range_percent)
  bin_edges_rows = get_bin_edges_from_centers(bin_centers_rows)
  bin_edges_cols = get_bin_edges_from_centers(bin_centers_cols)
  bin_indices_rows = numpy.searchsorted(bin_edges_rows, data_y, side="right") - 1
  bin_indices_cols = numpy.searchsorted(bin_edges_cols, data_x, side="right") - 1
  bin_indices_rows = numpy.clip(bin_indices_rows, 0, len(bin_centers_rows)-1)
  bin_indices_cols = numpy.clip(bin_indices_cols, 0, len(bin_centers_cols)-1)
  bin_counts = numpy.zeros((len(bin_centers_rows), len(bin_centers_cols)), dtype=float)
  if data_weights is not None:
    if (data_weights.size != data_x.size) or (data_weights.size != data_y.size):
      raise ValueError("The size of `data_weights` must match the size of the provided `data_{x,y}`.")
    numpy.add.at(bin_counts, (bin_indices_rows, bin_indices_cols), data_weights)
  else: numpy.add.at(bin_counts, (bin_indices_rows, bin_indices_cols), 1)
  bin_widths_cols = numpy.diff(bin_edges_cols)
  bin_widths_rows = numpy.diff(bin_edges_rows)
  bin_areas = numpy.outer(bin_widths_rows, bin_widths_cols)
  jpdf = bin_counts / (numpy.sum(bin_counts) * bin_areas)
  if smoothing_length is not None: jpdf = smooth_data.smooth_2d_data_with_gaussian_filter(jpdf, smoothing_length)
  return bin_centers_rows, bin_centers_cols, jpdf

def estimate_pdf(
    values            : numpy.ndarray,
    weights           : numpy.ndarray | None = None,
    num_bins          : int | None = None,
    bin_centers       : numpy.ndarray | None = None,
    bin_range_percent : float = 1.0,
    delta_threshold   : float = 1e-5,
  ):
  """Compute the 1D probability density function (PDF) for the provided `values`."""
  if len(values) == 0: raise ValueError("Cannot compute a PDF for an empty dataset.")
  if numpy.std(values) < delta_threshold:
    ## little variantion in the values implies a delta function
    mean_value = numpy.mean(values)
    epsilon_width = 1e-4 * (1.0 if mean_value == 0 else numpy.abs(mean_value))
    ## create three bins around the delta value
    bin_centers = numpy.array([
      mean_value - epsilon_width,
      mean_value,
      mean_value + epsilon_width
    ])
    pdf = numpy.array([ 0.0, 1/epsilon_width, 0.0 ])
    return bin_centers, pdf
  if bin_centers is None:
    if num_bins is None: raise ValueError("You did not provide a binning option.")
    bin_centers = create_uniformly_spaced_bin_centers(values, num_bins, bin_range_percent)
  elif not numpy.all(bin_centers[:-1] <= bin_centers[1:]):
    raise ValueError("Bin edges must be sorted in ascending order.")
  bin_widths = numpy.diff(bin_centers)
  bin_widths = numpy.append(bin_widths, bin_widths[-1])
  if numpy.any(bin_widths <= 0): raise ValueError("All bin widths must be positive.")
  bin_edges   = get_bin_edges_from_centers(bin_centers)
  bin_indices = numpy.searchsorted(bin_edges, values, side="right") - 1
  bin_indices = numpy.clip(bin_indices, 0, len(bin_centers)-1)
  bin_counts  = numpy.zeros(len(bin_centers), dtype=float)
  if weights is not None:
    if len(weights) != len(values): raise ValueError(f"The length of `weights` ({len(weights)}) must match the length of `values` ({len(values)}).")
    numpy.add.at(bin_counts, bin_indices, weights)
  else: numpy.add.at(bin_counts, bin_indices, 1)
  total_counts = numpy.sum(bin_counts)
  if total_counts <= 0: raise ValueError("None of the `values` fell into any bins. Check binning options or `values`:", values)
  pdf = bin_counts / (total_counts * bin_widths)
  return bin_centers, pdf

def get_bin_edges_from_centers(bin_centers: numpy.ndarray) -> numpy.ndarray:
  """Convert bin centers to edges."""
  bin_widths     = numpy.diff(bin_centers)
  left_bin_edge  = bin_centers[0]  - 0.5 * bin_widths[0]
  right_bin_edge = bin_centers[-1] + 0.5 * bin_widths[-1]
  return numpy.concatenate([
    [ left_bin_edge ],
    bin_centers[:-1] + 0.5 * bin_widths,
    [ right_bin_edge ]
  ])

def create_uniformly_spaced_bin_centers(
    values            : numpy.ndarray,
    num_bins          : int,
    bin_range_percent : float = 1.0,
  ):
  p16_value = numpy.percentile(values, 16)
  p50_value = numpy.percentile(values, 50)
  p84_value = numpy.percentile(values, 84)
  return numpy.linspace(
    start = p16_value - (1 + bin_range_percent) * (p50_value - p16_value),
    stop  = p84_value + (1 + bin_range_percent) * (p84_value - p50_value),
    num   = int(num_bins)
  )


## END OF MODULE