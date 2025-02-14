#!/usr/bin/env python3

## ###############################################################
## MODULES
## ###############################################################
import os, sys, glob

## load user defined modules
from TheFlashModule import FlashData


## ###############################################################
## PROGRAM PARAMTERS
## ###############################################################
BOOL_MPROC = 1

## full list of simulations
LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/", "/scratch/ek9/nk7952/" ]
LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
LIST_RES_FOLDERS   = [ "18", "36", "72", "144", "288", "576", "1152" ]
LIST_SIM_NAMES     = [  ]


## ###############################################################
## MAIN PROGRAM FUNCTIONS
## ###############################################################
def readFile(filepath):
  if ("_plt_cnt_" in filepath) and (".dat" in filepath): return 0
  with open(filepath, "rb") as fp:
    file_contents = fp.read(10)
  #   if "useViscosity" in file_contents: print("here")
  return 1

def countFilesInDirectory(directory, total_files):
  num_files_in_directory = 0
  list_filepaths = glob.glob(f"{directory}/*")
  for filepath in list_filepaths:
    if os.path.isfile(filepath) and any(
        str_pattern in filepath
        for str_pattern in [
        # "flash4_",
        # "flash.par",
        # ".dat",
        # ".log",
        # "driving.par",
        # "driving_history.txt",
        # "_chk_",
        # "_plt_cnt_",
        # ".json",
        ".h5",
      ]):
      ## count the number of versions of each file-type
      val = readFile(filepath)
      total_files += val
      num_files_in_directory += val
    elif os.path.isdir(filepath): total_files = countFilesInDirectory(filepath, total_files)
  print(f"{num_files_in_directory} files in {directory}")
  return total_files

def countSimFiles(directory_sim, **kwargs):
  total_files = countFilesInDirectory(directory_sim, total_files=0)
  print(f"Total number of files: {total_files}")

def main():
  FlashData.callFuncForAllSimulations(
    func               = countSimFiles,
    bool_mproc         = BOOL_MPROC,
    list_base_paths    = LIST_BASE_PATHS,
    list_suite_folders = LIST_SUITE_FOLDERS,
    list_mach_folders  = LIST_MACH_FOLDERS,
    list_sim_folders   = LIST_SIM_FOLDERS,
    list_res_folders   = LIST_RES_FOLDERS
  )


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM