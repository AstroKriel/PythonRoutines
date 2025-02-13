#!/usr/bin/env python3

## ###############################################################
## MODULES
## ###############################################################
import os, sys, time, glob


## ###############################################################
## PROGRAM PARAMETERS
## ###############################################################
CURRENT_TIME = time.mktime(time.localtime())
BOOL_TOUCH   = 1


## ###############################################################
## MAIN PROGRAM FUNCTIONS
## ###############################################################
def touch(filepath):
  if BOOL_TOUCH:
    try: os.utime(filepath, (CURRENT_TIME, CURRENT_TIME))
    except: print("Error: couldn't modify filepath, probably due to file permission issues:", filepath)
  else: print(filepath)

def touchFilesInDirectory(directory, num_files_touched, num_directories_touched):
  print("Looking at:", directory)
  list_filepaths = glob.glob(f"{directory}/*")
  for filepath in list_filepaths:
    touch(filepath)
    if os.path.isdir(filepath):
      num_directories_touched += 1
      num_files_touched, num_directories_touched = touchFilesInDirectory(filepath, num_files_touched, num_directories_touched)
    elif os.path.isfile(filepath): num_files_touched += 1
  return num_files_touched, num_directories_touched


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  start_time_sec = time.time()
  num_files_touched, num_directories_touched = touchFilesInDirectory(directory=".", num_files_touched=0, num_directories_touched=0)
  print(f"Number of files: {num_files_touched:.3E}")
  print(f"Number of directories: {num_directories_touched:.3E}")
  print(f"Execution time: {time.time() - start_time_sec:.2f} seconds")
  sys.exit(0)


## END OF PROGRAM