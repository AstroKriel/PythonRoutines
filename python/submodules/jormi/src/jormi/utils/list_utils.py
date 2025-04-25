## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
from jormi.utils import var_utils


## ###############################################################
## FUNCTIONS
## ###############################################################
def get_index_of_closest_value(
    values: list | numpy.ndarray,
    target: float,
  ) -> int:
  """Find the index of the closest value to a `target` value."""
  var_utils.assert_type(values, (list, numpy.ndarray))
  var_utils.assert_type(target, (int, float))
  if len(values) == 0: raise ValueError("Input list cannot be empty")
  array = numpy.asarray(values)
  if target is None: return None
  if target ==  numpy.inf: return int(numpy.nanargmax(array))
  if target == -numpy.inf: return int(numpy.nanargmin(array))
  return int(numpy.nanargmin(numpy.abs(array - target)))

def find_first_crossing(
    values    : list[float] | numpy.ndarray,
    target    : float,
    direction : str | None = None
  ):
  values = numpy.asarray(values)
  min_value = numpy.min(values)
  max_value = numpy.max(values)
  if not (min_value <= target <= max_value):
    raise ValueError(f"`target` ({target:.2f}) is outside the range of the input values: [{min_value:.2f}, {max_value:.2f}].")
  valid_filters = [ "rising", "falling", None ]
  if direction not in valid_filters:
     raise ValueError(f"`direction` must be one of {valid_filters}, but got {direction!r}. Choose from {cast_to_string(valid_filters)}")
  if target == min_value: return numpy.argmin(values)
  if target == max_value: return numpy.argmax(values)
  for value_index in range(len(values)-1):
    value_left  = values[value_index]
    value_right = values[value_index+1]
    crossed_target_while_rising = (value_left < target <= value_right)
    crossed_target_while_falling = (value_right < target <= value_left)
    if (direction == "rising") and crossed_target_while_rising:
      return value_index
    elif (direction == "falling") and crossed_target_while_falling:
      return value_index
    elif (direction is None) and (crossed_target_while_rising or crossed_target_while_falling):
      return value_index
  return None

def cast_to_string(
    elems            : list | numpy.ndarray,
    conjunction      : str = "or",
    wrap_in_quotes   : bool = True,
    use_oxford_comma : bool = True,
  ):
  elems = flatten_list(list(elems))
  if len(elems) == 0: return ""
  elems = [
    f"`{elem}`" if wrap_in_quotes else str(elem)
    for elem in elems
  ]
  if (conjunction != "") and (len(elems) > 1):
    if len(elems) == 2: return f"{elems[0]} {conjunction} {elems[1]}"
    if use_oxford_comma and len(elems) > 2:
      return ", ".join(elems[:-1]) + f", {conjunction} {elems[-1]}"
    else: return ", ".join(elems[:-1]) + f" {conjunction} {elems[-1]}"
  return ", ".join(elems)

def get_intersect_of_lists(
    list_a: list | numpy.ndarray,
    list_b: list | numpy.ndarray,
    sort_values: bool = False,
  ) -> list:
  """Find the intersection of two lists (optionally sorted)."""
  var_utils.assert_type(list_a, (list, numpy.ndarray))
  var_utils.assert_type(list_b, (list, numpy.ndarray))
  if (len(list_a) == 0) or (len(list_b) == 0): return []
  set_intersect = set(list_a) & set(list_b)
  return sorted(set_intersect) if sort_values else list(set_intersect)

def get_union_of_lists(
    list_a: list | numpy.ndarray,
    list_b: list | numpy.ndarray,
    sort_values: bool = False,
  ) -> list:
  """Find the union of two lists (optionally sorted)."""
  var_utils.assert_type(list_a, (list, numpy.ndarray))
  var_utils.assert_type(list_b, (list, numpy.ndarray))
  if (len(list_a) == 0) or (len(list_b) == 0): return list(list_a) + list(list_b)
  set_union = set(list_a) | set(list_b)
  return sorted(set_union) if sort_values else list(set_union)

def flatten_list(elems : list | numpy.ndarray) -> list:
  """Flatten a nested list into a single list."""
  var_utils.assert_type(elems, (list, numpy.ndarray))
  flat_elems = []
  for elem in list(elems):
    if isinstance(elem, (list, numpy.ndarray)):
      flat_elems.extend(list(flatten_list(elem)))
    else: flat_elems.append(elem)
  return flat_elems


## END OF MODULE