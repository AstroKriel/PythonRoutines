## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import copy
from jormi.utils import var_utils, func_utils


## ###############################################################
## FUNCTIONS
## ###############################################################
@func_utils.warn_if_result_is_unused
def merge_dicts(
    dict_a: dict,
    dict_b: dict,
  ) -> dict:
  """Recursively merge two dictionaries (without modifying the inputs; where relevant, `dict_b` will be prefered)."""
  var_utils.assert_type(dict_a, dict)
  var_utils.assert_type(dict_b, dict)
  merged_dict = dict_a.copy()
  for key, value in dict_b.items():
    if key in merged_dict:
      ## both elements are dictionaries: merge them recursively
      if isinstance(merged_dict[key], dict) and isinstance(value, dict):
        merged_dict[key] = merge_dicts(merged_dict[key], value)
      ## both elements are lists: concatenate them
      elif isinstance(merged_dict[key], list) and isinstance(value, list):
        merged_dict[key] = merged_dict[key] + value
      ## both elements are sets: get union of them
      elif isinstance(merged_dict[key], set) and isinstance(value, set):
        merged_dict[key] = merged_dict[key] | value
      ## other types, deepcopy to avoid modifying original dict_a
      elif isinstance(value, (dict, list, set)):
        merged_dict[key] = copy.deepcopy(value)
      ## replace directly
      else: merged_dict[key] = value
    else: merged_dict[key] = value
  return merged_dict

def are_dicts_different(
      dict_a: dict,
      dict_b: dict,
    ) -> bool:
    ## check that the dictionaries have the same number of keys
    if len(dict_a) != len(dict_b): return True
    ## check if any key in dict_b is not in dict_a or if their values are different
    for key in dict_b:
      if (key not in dict_a) or (dict_b[key] != dict_a[key]):
        return True
    ## otherwise the dictionaries are the same
    return False


## END OF MODULE