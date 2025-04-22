## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy


## ###############################################################
## FUNCTIONS
## ###############################################################
def second_order_centered_difference(
    sfield_q   : numpy.ndarray,
    cell_width : float,
    grad_axis  : int,
  ) -> numpy.ndarray:
  forward  = -1
  backward = +1
  q_p = numpy.roll(sfield_q, int(1 * forward),  axis=grad_axis)
  q_m = numpy.roll(sfield_q, int(1 * backward), axis=grad_axis)
  return (q_p - q_m) / (2 * cell_width)

def fourth_order_centered_difference(
    sfield_q   : numpy.ndarray,
    cell_width : float,
    grad_axis  : int,
  ) -> numpy.ndarray:
  forward  = -1
  backward = +1
  q_p1 = numpy.roll(sfield_q, int(1 * forward),  axis=grad_axis)
  q_p2 = numpy.roll(sfield_q, int(2 * forward),  axis=grad_axis)
  q_m1 = numpy.roll(sfield_q, int(1 * backward), axis=grad_axis)
  q_m2 = numpy.roll(sfield_q, int(2 * backward), axis=grad_axis)
  return (-q_p2 + 8*q_p1 - 8*q_m1 + q_m2) / (12 * cell_width)

def sixth_order_centered_difference(
    sfield_q   : numpy.ndarray,
    cell_width : float,
    grad_axis  : int,
  ) -> numpy.ndarray:
  forward  = -1
  backward = +1
  q_p1 = numpy.roll(sfield_q, int(1 * forward),  axis=grad_axis)
  q_p2 = numpy.roll(sfield_q, int(2 * forward),  axis=grad_axis)
  q_p3 = numpy.roll(sfield_q, int(3 * forward),  axis=grad_axis)
  q_m1 = numpy.roll(sfield_q, int(1 * backward), axis=grad_axis)
  q_m2 = numpy.roll(sfield_q, int(2 * backward), axis=grad_axis)
  q_m3 = numpy.roll(sfield_q, int(3 * backward), axis=grad_axis)
  return (q_p3 - 9*q_p2 + 45*q_p1 - 45*q_m1 + 9*q_m2 - q_m3) / (60 * cell_width)


## END OF MODULE