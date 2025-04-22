## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
from jormi.utils import func_utils
from jormi.ww_fields import field_operators, decompose_fields


## ###############################################################
## FUNCTIONS
## ###############################################################
@func_utils.time_function
def compute_magnetic_curvature_terms(
    vbasis_normal  : numpy.ndarray,
    vbasis_tangent : numpy.ndarray,
    vfield_u       : numpy.ndarray,
    box_width      : float = 1.0,
    grad_order     : int = 2,
  ) -> tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
  ## du_j/dx_i: (component-j, gradient-direction-i, x, y, z)
  r2tensor_grad_u = field_operators.compute_vfield_gradient(vfield_u, box_width, grad_order)
  ## n_i n_j du_j/dx_i
  sfield_curvature = numpy.einsum("ixyz,jxyz,jixyz->xyz", vbasis_normal, vbasis_normal, r2tensor_grad_u)
  ## t_i t_j du_j/dx_i
  sfield_stretching = numpy.einsum("ixyz,jxyz,jixyz->xyz", vbasis_tangent, vbasis_tangent, r2tensor_grad_u)
  ## du_i/dx_i
  sfield_compression = numpy.einsum("iixyz->xyz", r2tensor_grad_u)
  return sfield_curvature, sfield_stretching, sfield_compression

@func_utils.time_function
def compute_lorentz_force_terms(
    vfield_b   : numpy.ndarray,
    box_width  : float = 1.0,
    grad_order : int = 2,
  ) -> tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
  vbasis_tangent, vbasis_normal, _, sfield_kappa = decompose_fields.compute_tnb_terms(vfield_b, box_width, grad_order)
  sfield_sq_magn_b           = numpy.square(field_operators.compute_vfield_magnitude(vfield_b))
  vfield_tot_grad_pressure   = 0.5 * field_operators.compute_sfield_gradient(sfield_sq_magn_b, box_width, grad_order)
  vfield_align_grad_pressure = numpy.einsum("ixyz,jxyz,jxyz->ixyz", vbasis_tangent, vbasis_tangent, vfield_tot_grad_pressure)
  vfield_tension_force       = sfield_sq_magn_b * sfield_kappa * vbasis_normal
  vfield_ortho_grad_pressure = vfield_tot_grad_pressure - vfield_align_grad_pressure
  vfield_lorentz_force       = vfield_tension_force - vfield_ortho_grad_pressure
  del vbasis_tangent, vbasis_normal, sfield_kappa, sfield_sq_magn_b, vfield_tot_grad_pressure, vfield_align_grad_pressure
  return vfield_lorentz_force, vfield_tension_force, vfield_ortho_grad_pressure

def compute_dissipation_function(vfield_u : numpy.ndarray) -> numpy.ndarray:
  r2tensor_gradj_ui = field_operators.compute_vfield_gradient(vfield_u)
  sfield_div_u = numpy.einsum("iixyz->xyz", r2tensor_gradj_ui)
  r2tensor_bulk = 1/3 * numpy.einsum("xyz,ij->ijxyz", sfield_div_u, numpy.identity(3))
  ## S_ij = 0.5 ( \partial_i f_j + \partial_j f_i ) - 1/3 \delta_{ij} \partial_k f_k
  r2tensor_srt = 0.5 * (r2tensor_gradj_ui.transpose(1, 0, 2, 3, 4) + r2tensor_gradj_ui) - r2tensor_bulk
  ## \partial_j S_ij
  vfield_df = numpy.array([
    numpy.sum(field_operators.compute_vfield_gradient(r2tensor_srt[:,0,:,:,:])[0], axis=0),
    numpy.sum(field_operators.compute_vfield_gradient(r2tensor_srt[:,1,:,:,:])[1], axis=0),
    numpy.sum(field_operators.compute_vfield_gradient(r2tensor_srt[:,2,:,:,:])[2], axis=0),
  ])
  del vfield_u, r2tensor_gradj_ui, sfield_div_u, r2tensor_bulk, r2tensor_srt, vfield_df
  return vfield_df


## END OF MODULE