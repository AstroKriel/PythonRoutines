## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy


## ###############################################################
## FUNCTIONS
## ###############################################################
def apply_2d_convolution(
    data             : numpy.ndarray,
    smoothing_kernel : numpy.ndarray
  ) -> numpy.ndarray:
  kernel_nrows, kernel_ncols = smoothing_kernel.shape
  pad_nrows   = kernel_nrows // 2
  pad_ncols   = kernel_ncols // 2
  padded_data = numpy.pad(data, ((pad_nrows, pad_nrows), (pad_ncols, pad_ncols)), mode="wrap")
  data_nrows, data_ncols = data.shape
  output = numpy.zeros((data_nrows, data_ncols), dtype=numpy.float64)
  for index_row in range(data_nrows):
    for index_col in range(data_ncols):
      data_subset = padded_data[index_row:index_row+kernel_nrows, index_col:index_col+kernel_ncols]
      output[index_row, index_col] = numpy.sum(data_subset * smoothing_kernel)
  return output

def define_2d_gaussian_kernel(
    size  : int,
    sigma : float
  ) -> numpy.ndarray:
  x_values = numpy.linspace(-(size // 2), size // 2, size)
  y_values = numpy.linspace(-(size // 2), size // 2, size)
  grid_x, grid_y = numpy.meshgrid(x_values, y_values)
  smoothing_kernel = numpy.exp(-(grid_x**2 + grid_y**2) / (2 * sigma**2))
  smoothing_kernel /= numpy.sum(smoothing_kernel)
  return smoothing_kernel

def smooth_2d_data_with_gaussian_filter(
    data  : numpy.ndarray,
    sigma : float
  ) -> numpy.ndarray:
  kernel_size      = int(6 * sigma) + 1
  smoothing_kernel = define_2d_gaussian_kernel(kernel_size, sigma)
  smoothed_data    = apply_2d_convolution(data, smoothing_kernel)
  return smoothed_data


## END OF MODULE