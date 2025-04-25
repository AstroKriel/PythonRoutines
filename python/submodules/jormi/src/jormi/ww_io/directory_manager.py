## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
from pathlib import Path


## ###############################################################
## FUNCTIONS
## ###############################################################
def does_directory_exist(
    directory   : str | Path,
    raise_error : bool = False
  ) -> bool:
  directory = Path(directory).absolute()
  result = directory.is_dir()
  if not(result) and raise_error: raise NotADirectoryError(f"Directory does not exist: {directory}")
  return result

def init_directory(
    directory : str,
    verbose   : bool = True
  ):
  directory = Path(directory).absolute()
  if not does_directory_exist(directory):
    directory.mkdir(parents=True)
    if verbose: print("Successfully initialised directory:", directory)
  elif verbose: print("No need to initialise diectory (already exists):", directory)


## END OF MODULE