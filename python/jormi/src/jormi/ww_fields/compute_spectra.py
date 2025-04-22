## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
import functools

try:
  from mpi4py import MPI
  MPI_AVAILABLE = True
  MPI_WORLD     = MPI.COMM_WORLD
  MPI_RANK      = MPI_WORLD.Get_rank()
  MPI_NUM_PROCS = MPI_WORLD.Get_size()
except ImportError:
  MPI_AVAILABLE = False
  MPI_WORLD     = None
  MPI_RANK      = 0
  MPI_NUM_PROCS = 1


## ###############################################################
## FUNCTIONS
## ###############################################################
@functools.lru_cache(maxsize=10)
def _compute_radial_grid(shape):
  k_center = numpy.array([ (n-1)/2 for n in shape ], dtype=float)
  grid_kz, grid_ky, grid_kx = numpy.indices(shape)
  return numpy.sqrt(
    numpy.square(grid_kx - k_center[0]) +
    numpy.square(grid_ky - k_center[1]) +
    numpy.square(grid_kz - k_center[2])
  )

def _compute_3d_power_spectrum(
    field   : numpy.ndarray,
    use_mpi : bool = False,
  ) -> numpy.ndarray:
  """Computes the power spectrum of an arbitrary-dimensional field."""
  assert len(field.shape) >= 3, "Field should have at least 3 spatial dimensions."
  fft_field = numpy.fft.fftshift(
    numpy.fft.fftn(field, axes=(-3, -2, -1), norm="forward"),
    axes = (-3, -2, -1)
  )
  spectrum = numpy.sum(
    numpy.square(numpy.abs(fft_field)),
    axis = tuple(range(len(field.shape) - 3))
  )
  if use_mpi and MPI_AVAILABLE:
    spectrum_global = numpy.empty_like(spectrum)
    MPI_WORLD.Allreduce(spectrum, spectrum_global, op=MPI.SUM)
    ## avoid redundant operations by only having the root process return the final global result
    return spectrum_global if MPI_WORLD.Get_rank() == 0 else None
  else: return spectrum

def _compute_spherical_integration(
    spectrum_3d : numpy.ndarray,
    use_mpi     : bool = False,
  ) -> tuple[numpy.ndarray, numpy.ndarray]:
  """Integrates a 3D power spectrum over spherical shells of constant k."""
  num_k_modes   = numpy.min(spectrum_3d.shape) // 2
  k_bin_edges   = numpy.linspace(0.5, num_k_modes, num_k_modes+1)
  k_bin_centers = numpy.ceil((k_bin_edges[:-1] + k_bin_edges[1:]) / 2.0)
  grid_k_magn   = _compute_radial_grid(spectrum_3d.shape)
  bin_indices   = numpy.digitize(grid_k_magn, k_bin_edges)
  spectrum = numpy.bincount(
    bin_indices.ravel(),
    weights   = spectrum_3d.ravel(),
    minlength = num_k_modes + 1
  )[1:-1]
  if use_mpi and MPI_AVAILABLE:
    spectrum_global = numpy.empty_like(spectrum)
    MPI_WORLD.Allreduce(spectrum, spectrum_global, op=MPI.SUM)
    ## avoid redundant operations by only having the root process return the final global result
    return k_bin_centers, spectrum_global if MPI_WORLD.Get_rank() == 0 else None, None
  return k_bin_centers, spectrum

def compute_1d_power_spectrum(
    field   : numpy.ndarray,
    use_mpi : bool = False,
  ) -> tuple[numpy.ndarray, numpy.ndarray]:
  """Computes the full power spectrum including radial integration."""
  spectrum_3d = _compute_3d_power_spectrum(field, use_mpi)
  if spectrum_3d is None: return None, None
  k_bin_centers, spectrum_1d = _compute_spherical_integration(spectrum_3d, use_mpi)
  if (k_bin_centers is None) or (spectrum_1d is None): return None, None
  return k_bin_centers, spectrum_1d


## END OF MODULE