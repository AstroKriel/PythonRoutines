## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
import shutil
from pathlib import Path
from jormi.utils import list_utils, var_utils
from jormi.ww_io import directory_manager


## ###############################################################
## UTILITY FUNCTIONS
## ###############################################################
def combine_file_path_parts(file_path_parts : list[str] | list[Path]) -> Path:
  return Path(*list_utils.flatten_list(file_path_parts)).absolute()

def resolve_file_path(
    file_path : str | Path | None = None,
    directory : str | Path | None = None,
    file_name : str | None = None,
  ):
  if file_path is None:
    missing = []
    if (directory is None): missing.append("directory")
    if (file_name is None): missing.append("file_name")
    if missing:
      raise ValueError(
        "You have not provided enough information about the file and where it is. "
        f"You are missing: {list_utils.cast_to_string(missing)}. "
        "Alternatively, provide `file_path` directly."
      )
    file_path = combine_file_path_parts([ directory, file_name ])
  else: file_path = Path(file_path).absolute()
  return file_path

def does_file_exist(
    file_path   : str | Path | None = None,
    directory   : str | Path | None = None,
    file_name   : str | None = None,
    raise_error : bool = False,
  ) -> bool:
  file_path = resolve_file_path(file_path=file_path, directory=directory, file_name=file_name)
  file_path_exists = file_path.is_file()
  if not(file_path_exists) and raise_error:
    raise FileNotFoundError(f"File does not exist: {file_path}")
  return file_path_exists

def copy_file(
    directory_from : str | Path,
    directory_to   : str | Path,
    file_name      : str,
    overwrite      : bool = False,
    verbose        : bool = True,
  ):
  directory_manager.does_directory_exist(directory=directory_from, raise_error=True)
  if not directory_manager.does_directory_exist(directory=directory_to):
    directory_manager.init_directory(directory=directory_to, verbose=verbose)
  file_path_from = combine_file_path_parts([ directory_from, file_name ])
  file_path_to   = combine_file_path_parts([ directory_to, file_name ])
  does_file_exist(file_path=file_path_from, raise_error=True)
  if not(overwrite) and does_file_exist(file_path=file_path_to, raise_error=False):
    raise FileExistsError(f"File already exists: {file_path_to}")
  shutil.copy(file_path_from, file_path_to)
  shutil.copymode(file_path_from, file_path_to)
  if verbose:
    print(f"Copied:")
    print(f"\t> File: {file_name}")
    print(f"\t> From: {directory_from}")
    print(f"\t> To:   {directory_to}")


## ###############################################################
## FILTER FILES IN A DIRECTORY
## ###############################################################
def _create_filter(
    include_string, exclude_string,
    prefix, suffix,
    delimiter, num_parts,
    index_of_value, min_value, max_value,
  ):
  def _does_file_meet_criteria(file_name):
    file_name_parts = file_name.split(delimiter)
    ## make sure that basic conditions are met first
    if include_string and (include_string not in file_name): return False
    if exclude_string and (exclude_string in file_name): return False
    if prefix and not file_name.startswith(prefix): return False
    if suffix and not file_name.endswith(suffix): return False
    if (num_parts is not None) and (len(file_name_parts) != num_parts): return False
    ## if a part of the file name should be a value, then check that the value falls within the specified value range
    if index_of_value is not None:
      if len(file_name_parts) < abs(index_of_value): return False
      try:
        value = int(file_name_parts[index_of_value])
      except ValueError: return False
      if not (min_value <= value <= max_value): return False
    return True
  return _does_file_meet_criteria

def filter_files(
    directory      : str | Path,
    include_string : str | None = None,
    exclude_string : str | None = None,
    prefix         : str | None = None,
    suffix         : str | None = None,
    delimiter      : str = "_",
    num_parts      : int | None = None,
    index_of_value : int | None = None,
    min_value      : int = 0,
    max_value      : int = numpy.inf,
  ) -> list[str]:
  """
    Filter file names in a `directory` based on various conditions:
    - `include_string` : File names must contain this string.
    - `exclude_string` : File names should not contain this string.
    - `prefix`         : File names should start with this string.
    - `suffix`         : File names should end with this string.
    - `delimiter`      : The delimiter used to split the file name (default: "_").
    - `num_parts`      : Only include files that, when split by `delimiter`, have exactly this number of parts.
    - `index_of_value` : The part-index to check for value range conditions.
    - `min_value`      : The minimum valid value (inclusive) stored at `index_of_value`.
    - `max_value`      : The maximum valid value (inclusive) stored at `index_of_value`.
  """
  directory = Path(directory).absolute()
  directory_manager.does_directory_exist(directory, raise_error=True)
  var_utils.assert_type(min_value, (int, float), "min_value")
  var_utils.assert_type(max_value, (int, float), "max_value")
  if min_value > max_value: raise ValueError(f"`min_value` = {min_value} must be less than `max_value` = {max_value}.")
  file_filter = _create_filter(
    include_string = include_string,
    exclude_string = exclude_string,
    prefix         = prefix,
    suffix         = suffix,
    delimiter      = delimiter,
    num_parts      = num_parts,
    index_of_value = index_of_value,
    min_value      = min_value,
    max_value      = max_value,
  )
  file_names = [
    item.name
    for item in directory.iterdir()
    if item.is_file()
  ]
  return list(filter(file_filter, file_names))


## END OF MODULE