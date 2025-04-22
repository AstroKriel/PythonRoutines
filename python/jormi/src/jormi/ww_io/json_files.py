## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import json
import copy
import numpy
from pathlib import Path
from jormi.ww_io import file_manager
from jormi.utils import dict_utils


## ###############################################################
## FUNCTIONS
## ###############################################################
def _ensure_json_extension(path: Path):
  if path.suffix != ".json": raise ValueError(f"Expected .json file, got {path}")

def read_json_file_into_dict(
    file_path : str | Path | None = None,
    directory : str | Path | None = None,
    file_name : str | None = None,
    verbose   : bool = True,
  ):
  file_path = file_manager.resolve_file_path(file_path=file_path, directory=directory, file_name=file_name)
  _ensure_json_extension(file_path)
  if file_manager.does_file_exist(file_path=file_path):
    if verbose: print("Reading in json-file:", file_path)
    with open(file_path, "r") as file_pointer:
      return copy.deepcopy(json.load(file_pointer))
  else: raise FileNotFoundError(f"No json-file found: {file_path}")

class NumpyEncoder(json.JSONEncoder):
  def default(self, obj):
    if   isinstance(obj, numpy.integer):  return int(obj)
    elif isinstance(obj, numpy.floating): return float(obj)
    elif isinstance(obj, numpy.bool_):    return bool(obj)
    elif isinstance(obj, numpy.ndarray):  return obj.tolist()
    return super().default(obj)

def save_dict_to_json_file(
    file_path  : str | Path,
    input_dict : dict,
    verbose    : bool = True,
  ):
  if file_manager.does_file_exist(file_path):
    _add_dict_to_json_file(file_path, input_dict, verbose)
  else: _create_json_file_from_dict(file_path, input_dict, verbose)

def _dump_dict_to_json(
    file_path  : str | Path,
    input_dict : dict,
  ):
  file_path = Path(file_path).resolve()
  _ensure_json_extension(file_path)
  with open(file_path, "w") as file_pointer:
    json.dump(
      obj       = input_dict,
      fp        = file_pointer,
      cls       = NumpyEncoder,
      sort_keys = True,
      indent    = 2,
    )

def _create_json_file_from_dict(
    file_path  : str | Path,
    input_dict : dict,
    verbose    : bool = True,
  ):
  _dump_dict_to_json(file_path, input_dict)
  if verbose: print("Saved json-file:", file_path)

def _add_dict_to_json_file(
    file_path  : str | Path,
    input_dict : dict,
    verbose    : bool = True,
  ):
  old_dict = read_json_file_into_dict(file_path=file_path, verbose=False)
  merged_dict = dict_utils.merge_dicts(old_dict, input_dict)
  _dump_dict_to_json(file_path, merged_dict)
  if verbose: print("Updated json-file:", file_path)


## END OF MODULE