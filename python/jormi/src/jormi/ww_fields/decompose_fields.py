## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
from jormi.utils import func_utils
from jormi.ww_fields import field_operators


## ###############################################################
## FUNCTIONS
## ###############################################################
@func_utils.time_function
def compute_helmholtz_decomposition(
    vfield_q    : numpy.ndarray,
    domain_size : tuple[float, float, float],
  ) -> tuple[numpy.ndarray, numpy.ndarray]:
  if vfield_q.shape[0] != 3: raise ValueError("Input vector field must have shape: (3, num_cells_x, num_cells_y, num_cells_z)")
  if len(domain_size)  != 3: raise ValueError("Input domain size must have shape: (length_x, length_y, length_z)")
  num_cells_x, num_cells_y, num_cells_z = vfield_q.shape[1:]
  kx_values = 2 * numpy.pi * numpy.fft.fftfreq(num_cells_x) * num_cells_x / domain_size[0]
  ky_values = 2 * numpy.pi * numpy.fft.fftfreq(num_cells_y) * num_cells_y / domain_size[1]
  kz_values = 2 * numpy.pi * numpy.fft.fftfreq(num_cells_z) * num_cells_z / domain_size[2]
  grid_kx, grid_ky, grid_kz = numpy.meshgrid(kx_values, ky_values, kz_values, indexing="ij")
  grid_k_magn = grid_kx**2 + grid_ky**2 + grid_kz**2
  ## avoid division by zero
  ## note, numpy.fft.fftn will assume the zero frequency is at index 0
  grid_k_magn[0, 0, 0] = 1
  vfield_fft_q = numpy.fft.fftn(vfield_q, axes=(1, 2, 3), norm="forward")
  ## \vec{k} cdot \vec{F}(\vec{k})
  sfield_k_dot_fft_q = grid_kx * vfield_fft_q[0] + grid_ky * vfield_fft_q[1] + grid_kz * vfield_fft_q[2]
  ## divergence (curl-free) component: (\vec{k} / k^2) (\vec{k} \cdot \vec{F}(\vec{k}))
  vfield_fft_div = numpy.stack([
    (grid_kx / grid_k_magn) * sfield_k_dot_fft_q,
    (grid_ky / grid_k_magn) * sfield_k_dot_fft_q,
    (grid_kz / grid_k_magn) * sfield_k_dot_fft_q
  ])
  ## solenoidal (divergence-free) component: \vec{F}(\vec{k}) - (\vec{k} / k^2) (\vec{k} \cdot \vec{F}(\vec{k}))
  vfield_fft_sol = vfield_fft_q - vfield_fft_div
  ## transform back to real space
  vfield_div = numpy.fft.ifftn(vfield_fft_div, axes=(1,2,3), norm="forward").real
  vfield_sol = numpy.fft.ifftn(vfield_fft_sol, axes=(1,2,3), norm="forward").real
  del kx_values, ky_values, kz_values, grid_kx, grid_ky, grid_kz, grid_k_magn
  del vfield_fft_q, sfield_k_dot_fft_q, vfield_fft_div, vfield_fft_sol
  return vfield_div, vfield_sol

@func_utils.time_function
def compute_tnb_terms(
    vfield_b   : numpy.ndarray,
    box_width  : float = 1.0,
    grad_order : int = 2,
  ) -> tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray]:
  ## format: (vector-component, x, y, z)
  vfield_b = numpy.array(vfield_b)
  ## ---- COMPUTE TANGENT BASIS
  ## (f_k f_k)^(1/2)
  sfield_magn_b = field_operators.compute_vfield_magnitude(vfield_b)
  ## f_i / (f_k f_k)^(1/2)
  vbasis_tangent = vfield_b * sfield_magn_b**(-1)
  ## ---- COMPUTE NORMAL BASIS
  ## df_j/dx_i: (component-j, gradient-direction-i, x, y, z)
  r2tensor_grad_b = field_operators.compute_vfield_gradient(vfield_b, box_width, grad_order)
  ## f_i df_j/dx_i
  vbasis_normal_term1 = numpy.einsum("ixyz,jixyz->jxyz", vfield_b, r2tensor_grad_b)
  ## f_i f_j f_m df_m/dx_i
  vbasis_normal_term2 = numpy.einsum("ixyz,jxyz,mxyz,mixyz->jxyz", vfield_b, vfield_b, vfield_b, r2tensor_grad_b)
  ## (f_i df_j/dx_i) / (f_k f_k) - (f_i f_j f_m df_m/dx_i) / (f_k f_k)^2
  vfield_kappa = vbasis_normal_term1 * sfield_magn_b**(-2) - vbasis_normal_term2 * sfield_magn_b**(-4)
  ## clean up temporary quantities
  del vbasis_normal_term1, vbasis_normal_term2
  ## field curvature
  sfield_curvature = field_operators.compute_vfield_magnitude(vfield_kappa)
  ## normal basis
  vbasis_normal = vfield_kappa / sfield_curvature
  ## ---- COMPUTE BINORMAL BASIS
  ## by definition b-basis is orthogonal to both t- and n-basis
  vbasis_binormal = field_operators.compute_vfield_cross_product(vbasis_tangent, vbasis_normal)
  return vbasis_tangent, vbasis_normal, vbasis_binormal, sfield_curvature


## END OF MODULE