import sys
from pathlib import Path
from jormi.ww_io import io_manager

def get_sim_directories():
  directories = list(Path("/scratch").glob("*/nk7952/Re*/Mach*/Pm*/*"))
  return sorted(
    directory
    for directory in directories
    if io_manager.does_directory_exist(directory) and ("anti" not in str(directory))
  )

if __name__ == "__main__":
  parent_directory = io_manager.get_caller_directory().parent
  file_name = "ssd_sim_directories.txt"
  file_path = io_manager.combine_file_path_parts([ parent_directory, file_name ])
  with open(file_path, "w") as file_pointer:
    for directory in get_sim_directories():
      print(directory)
      file_pointer.write(str(directory) + "\n")
  print(" ")
  print(f"Saved: {file_path}")
  sys.exit(0)

## end of script