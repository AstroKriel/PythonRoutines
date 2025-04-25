## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
from jormi.ww_data import finite_difference


## ###############################################################
## FUNCTIONS
## ###############################################################
def compute_sfield_rms(sfield_q : numpy.ndarray) -> numpy.ndarray:
  return numpy.sqrt(numpy.mean(numpy.square(sfield_q)))

def compute_vfield_cross_product(
    vfield_q1 : numpy.ndarray,
    vfield_q2 : numpy.ndarray,
  ) -> numpy.ndarray:
  return numpy.array([
    vfield_q1[1] * vfield_q2[2] - vfield_q1[2] * vfield_q2[1],
    vfield_q1[2] * vfield_q2[0] - vfield_q1[0] * vfield_q2[2],
    vfield_q1[0] * vfield_q2[1] - vfield_q1[1] * vfield_q2[0]
  ])

def compute_vfield_dot_product(
    vfield_q1 : numpy.ndarray,
    vfield_q2 : numpy.ndarray,
  ) -> numpy.ndarray:
  return numpy.einsum("ixyz,ixyz->xyz", vfield_q1, vfield_q2)

def compute_vfield_magnitude(vfield_q : numpy.ndarray) -> numpy.ndarray:
  return numpy.sqrt(numpy.sum(numpy.multiply(vfield_q, vfield_q), axis=0))

def get_grad_func(grad_order: int):
  implemented_grad_funcs = {
    2: finite_difference.second_order_centered_difference,
    4: finite_difference.fourth_order_centered_difference,
    6: finite_difference.sixth_order_centered_difference,
  }
  if grad_order not in implemented_grad_funcs: raise ValueError(f"Gradient order `{grad_order}` is invalid.")
  grad_func = implemented_grad_funcs[grad_order]
  return grad_func

def compute_vfield_curl(
    vfield_q   : numpy.ndarray,
    box_width  : float = 1.0,
    grad_order : int = 2,
  ) -> numpy.ndarray:
  grad_func = get_grad_func(grad_order)
  ## input format: (vector-component, x, y, z), assuming cubic domain with uniform grid
  ## output format: (curl-component, x, y, z)
  vfield_q   = numpy.array(vfield_q)
  cell_width = box_width / vfield_q.shape[1]
  ## curl components
  return numpy.array([
    grad_func(vfield_q[2], cell_width, grad_axis=1) - grad_func(vfield_q[1], cell_width, grad_axis=2),
    grad_func(vfield_q[0], cell_width, grad_axis=2) - grad_func(vfield_q[2], cell_width, grad_axis=0),
    grad_func(vfield_q[1], cell_width, grad_axis=0) - grad_func(vfield_q[0], cell_width, grad_axis=1),
  ])

def compute_sfield_gradient(
    sfield_q   : numpy.ndarray,
    box_width  : float = 1.0,
    grad_order : int = 2,
  ):
  grad_func = get_grad_func(grad_order)
  ## input format: (x, y, z), assuming cubic domain with uniform grid
  ## output format: (gradient-direction, x, y, z)
  sfield_q = numpy.array(sfield_q)
  cell_width = box_width / sfield_q.shape[0]
  return numpy.array([
    grad_func(sfield_q, cell_width, grad_axis)
    for grad_axis in [0, 1, 2]
  ])

def compute_vfield_gradient(
    vfield_q   : numpy.ndarray,
    box_width  : float = 1.0,
    grad_order : int = 2,
  ):
  ## df_i/dx_j: (component-i, gradient-direction-j, x, y, z)
  return numpy.array([
    compute_sfield_gradient(sfield_qi, box_width, grad_order)
    for sfield_qi in vfield_q
  ])

def compute_vfield_divergence(
    vfield_q   : numpy.ndarray,
    box_width  : float = 1.0,
    grad_order : int = 2,
  ):
  r2tensor_grad_q = compute_vfield_gradient(vfield_q, box_width, grad_order)
  return numpy.einsum("iixyz->xyz", r2tensor_grad_q)


## END OF MODULE