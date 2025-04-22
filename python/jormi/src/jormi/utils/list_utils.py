## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
from jormi.utils import var_utils


## ###############################################################
## FUNCTIONS
## ###############################################################
def cast_to_string(
    elems            : list,
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
    separator = "," if use_oxford_comma else ""
    return ", ".join(elems[:-1]) + f"{separator} {conjunction} {elems[-1]}"
  return ", ".join(elems)

def get_intersect_of_lists(
    list_a: list,
    list_b: list,
    sort_values: bool = False,
  ) -> list:
  """Find the intersection of two lists (optionally sorted)."""
  var_utils.assert_type(list_a, list)
  var_utils.assert_type(list_b, list)
  if (len(list_a) == 0) or (len(list_b) == 0): return []
  set_intersect = set(list_a) & set(list_b)
  return sorted(set_intersect) if sort_values else list(set_intersect)

def get_union_of_lists(
    list_a: list,
    list_b: list,
    sort_values: bool = False,
  ) -> list:
  """Find the union of two lists (optionally sorted)."""
  var_utils.assert_type(list_a, list)
  var_utils.assert_type(list_b, list)
  if (len(list_a) == 0) or (len(list_b) == 0): return list_a + list_b
  set_union = set(list_a) | set(list_b)
  return sorted(set_union) if sort_values else list(set_union)

def get_index_of_closest_value(
    values: list,
    target: float,
  ) -> int:
  """Find the index of the closest value to a `target` value."""
  var_utils.assert_type(values, list)
  var_utils.assert_type(target, (int, float))
  if len(values) == 0: raise ValueError("Input list cannot be empty")
  array_vals = numpy.asarray(values)
  if target is None: return None
  if target ==  numpy.inf: return int(numpy.nanargmax(array_vals))
  if target == -numpy.inf: return int(numpy.nanargmin(array_vals))
  return int(numpy.nanargmin(numpy.abs(array_vals - target)))

def flatten_list(elems : list) -> list:
  """Flatten a nested list into a single list."""
  var_utils.assert_type(elems, (list, numpy.ndarray))
  flat_elems = []
  for elem in elems:
    if isinstance(elem, (list, numpy.ndarray)):
      flat_elems.extend(list(flatten_list(elem)))
    else: flat_elems.append(elem)
  return flat_elems


## END OF MODULE