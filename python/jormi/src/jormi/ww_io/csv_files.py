## START OF MODULE

## ###############################################################
## DEPENDENCIES
## ###############################################################
import csv
from pathlib import Path
from jormi.ww_io import file_manager


## ###############################################################
## FUNCTIONS
## ###############################################################
def _ensure_csv_extension(path: Path):
  if path.suffix != ".csv": raise ValueError(f"Expected .csv extension, got {path}")

def read_csv_file_into_dict(
    file_path : str | Path,
    verbose   : bool = True,
  ) -> dict:
  file_path = Path(file_path).resolve()
  _ensure_csv_extension(file_path)
  if not file_manager.does_file_exist(file_path):
    raise FileNotFoundError(f"No csv-file found: {file_path}")
  if verbose: print(f"Reading in csv-file: {file_path}")
  dataset = {}
  with open(file_path, "r", newline="") as file_pointer:
    reader = csv.DictReader(file_pointer)
    for key in reader.fieldnames:
      dataset[key] = []
    for row in reader:
      for key, value in row.items():
        dataset[key].append(float(value))
  return dataset

def save_dict_to_csv_file(
    file_path  : str | Path,
    input_dict : dict,
    overwrite  : bool = False,
    verbose    : bool = True,
  ):
  file_path = Path(file_path).resolve()
  _ensure_csv_extension(file_path)
  dataset_shape = [
    len(data_column)
    for data_column in input_dict.values()
  ]
  if len(set(dataset_shape)) != 1:
    raise ValueError("All dataset columns in `input_dict` should be the same length.")
  if file_manager.does_file_exist(file_path):
    if overwrite:
      _write_csv(file_path, input_dict)
      if verbose: print(f"Overwrote csv-file: {file_path}")
    else:
      _merge_dataset_into_csv(file_path, input_dict)
      if verbose: print(f"Updated csv-file: {file_path}")
  else:
    _write_csv(file_path, input_dict)
    if verbose: print(f"Saved csv-file: {file_path}")

def _write_csv(
    file_path  : Path,
    input_dict : dict
  ):
  with open(file_path, "w", newline="") as file_pointer:
    writer = csv.writer(file_pointer)
    writer.writerow(input_dict.keys())
    writer.writerows(zip(*input_dict.values()))

def _merge_dataset_into_csv(
    file_path  : Path,
    input_dict : dict,
  ):
  existing_dataset = read_csv_file_into_dict(file_path, verbose=False)
  ## validate shared keys match
  for key in existing_dataset:
    if key in input_dict:
      if existing_dataset[key] != input_dict[key]:
        raise ValueError(f"Mismatch in values for existing key: `{key}`")
  ## check that the new keys have the same number of dataset points
  existing_length = len(next(iter(existing_dataset.values())))
  for key in input_dict:
    if key not in existing_dataset:
      input_length = len(input_dict[key])
      if input_length != existing_length:
        raise ValueError(f"Length mismatch in new column `{key}`: expected length = {existing_length}, but got {input_length}.")
  ## merge new keys
  for key in input_dict:
    if key not in existing_dataset:
      existing_dataset[key] = input_dict[key]
  ## overwrite file with merged dataset
  _write_csv(file_path, existing_dataset)


## END OF MODULE