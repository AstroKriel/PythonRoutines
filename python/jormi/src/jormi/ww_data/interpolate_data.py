## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import warnings
import numpy
from scipy.interpolate import interp1d as scipy_interp1d
from jormi.utils import list_utils


## ###############################################################
## FUNCTIONS
## ###############################################################
def interpolate_1d(
    x_values : numpy.ndarray,
    y_values : numpy.ndarray,
    x_interp : numpy.ndarray,
    kind     : str = "cubic",
  ) -> numpy.ndarray:
  x_values = numpy.asarray(x_values, dtype=numpy.float64)
  y_values = numpy.asarray(y_values, dtype=numpy.float64)
  x_interp = numpy.asarray(x_interp, dtype=numpy.float64)
  if x_values.ndim != 1: raise ValueError("`x_values` should be a 1D array.")
  if x_interp.ndim != 1: raise ValueError("`x_interp` should be a 1D array.")
  if len(x_values) < 2: raise ValueError("Provided data should contain at least two points.")
  if len(x_values) != len(y_values): raise ValueError("`x_values` and `y_values` should have the same length.")
  if not numpy.all(numpy.diff(x_values) > 0): raise ValueError("`x_values` should be monotonically increasing.")
  valid_kinds = [ "linear", "quadratic", "cubic" ]
  if kind not in valid_kinds: raise ValueError(f"Invalid interpolation `kind`: {kind}. Valid options include: {list_utils.cast_to_string(valid_kinds)}")
  x_min_data = x_values[0]
  x_max_data = x_values[-1]
  in_bounds_mask = (x_min_data <= x_interp) & (x_interp <= x_max_data)
  num_out_of_bounds = numpy.sum(~in_bounds_mask)
  if num_out_of_bounds > 0: warnings.warn(f"Removing {num_out_of_bounds} `x_interp` points that are outside the interpolated domain.")
  interpolator = scipy_interp1d(
    x_values,
    y_values,
    kind          = kind,
    bounds_error  = False,
    assume_sorted = True
  )
  x_interp_in_bounds = x_interp[in_bounds_mask]
  y_interp_in_bounds = interpolator(x_interp_in_bounds)
  return x_interp_in_bounds, y_interp_in_bounds


## END OF MODULE