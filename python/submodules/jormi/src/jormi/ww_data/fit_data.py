## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
from scipy.optimize import curve_fit


## ###############################################################
## FUNCTIONS
## ###############################################################
def _linear_function(a0, a1, x):
  return a0 + a1 * numpy.array(x)

def fit_1d_linear_model(
    x_values    : list | numpy.ndarray,
    y_values    : list | numpy.ndarray,
    index_start : int = 0,
    index_end   : int | None = None
  ) -> dict:
  """Fits a linear function to data using least squares optimization."""
  if index_end is None: index_end = len(x_values)
  if len(x_values) != len(y_values): raise ValueError("`x_values` and `y_values` must have the same length.")
  ## note: truncates values locally: if input arguments are lists, then they will not be mutated
  x_values = x_values[index_start:index_end]
  y_values = y_values[index_start:index_end]
  fitted_params, fit_covariance = curve_fit(_linear_function, x_values, y_values)
  intercept, slope = fitted_params
  if fit_covariance is not None:
    intercept_std, slope_std = numpy.sqrt(numpy.diag(fit_covariance))
  else: intercept_std, slope_std = (None, None)
  residual = numpy.sum(numpy.square(y_values - _linear_function(x_values, *fitted_params)))
  return {
    "intercept": {
      "best": intercept,
      "std": intercept_std
    },
    "slope": {
      "best": slope,
      "std": slope_std
    },
    "residual": residual
  }


## END OF MODULE