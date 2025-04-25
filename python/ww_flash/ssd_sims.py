import sys
from pathlib import Path
from jormi.ww_io import directory_manager

def get_sim_directories():
  directories = list(Path("/scratch").glob("*/nk7952/Re*/Mach*/Pm*/*"))
  return sorted(
    directory
    for directory in directories
    if directory_manager.does_directory_exist(directory) and ("anti" not in str(directory))
  )

if __name__ == "__main__":
  for directory in get_sim_directories():
    print(directory)
  sys.exit(0)

## end of script