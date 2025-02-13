#!/usr/bin/env python3

## ###############################################################
## MODULES
## ###############################################################
import os, sys

## load user defined modules
from TheUsefulModule import WWFnF, WWTerminal
from TheFlashModule import FlashData


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def countFilesInDirectory(directory):
  return sum([
    len(files)
    for _, _, files in os.walk(directory)
  ])


## ###############################################################
## OPERATOR FUNCTION
## ###############################################################
def moveFilesBetweenProjects(directory_sim):
  print("Looking at:", directory_sim)
  print("Running in debug mode.")
  for directory_from in [
      f"{directory_sim}/plt",
      f"{directory_sim}/spect",
    ]:
    num_files = countFilesInDirectory(directory_from)
    if num_files == 0:
      print("\t> There are no files to move from:", directory_from)
      return
    directory_to = directory_from.replace(f"/{PROJECT_FROM}/", f"/{PROJECT_TO}/")
    print(f"\t> Moving {num_files} files under:", directory_from)
    print("\t> To:", directory_to)
    WWFnF.createDirectory(directory_to, bool_verbose=False)
    command = f"mv {directory_from}/* {directory_to}/."
    if BOOL_DEBUG_MODE: print(command)
    else: WWTerminal.runCommand(command)
    print(" ")



## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  list_directory_sims = FlashData.getListOfSimDirectories(
    list_base_paths    = [ f"/scratch/{PROJECT_FROM}/nk7952/" ],
    list_suite_folders = LIST_SUITE_FOLDERS,
    list_mach_folders  = LIST_MACH_FOLDERS,
    list_sim_folders   = LIST_SIM_FOLDERS,
    list_res_folders   = LIST_RES_FOLDERS
  )
  for directory_sim in list_directory_sims:
    moveFilesBetweenProjects(directory_sim)
    print(" ")


## ###############################################################
## PROGRAM PARAMTERS
## ###############################################################
BOOL_DEBUG_MODE = 0

LIST_PROJECTS = [ "jh2", "ek9" ]
PROJECT_FROM  = LIST_PROJECTS[1]
PROJECT_TO    = LIST_PROJECTS[0]

LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
LIST_RES_FOLDERS   = [ "576" ]

LIST_SIM_NAMES = [ ]


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM