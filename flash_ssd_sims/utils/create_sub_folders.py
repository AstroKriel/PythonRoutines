## ###############################################################
## MODULES
## ###############################################################
import sys

## load user defined modules
from Loki.TheUsefulModule import WWFnF
from Loki.TheFlashModule import FlashData


## ###############################################################
## PROGRAM PARAMETERS
## ###############################################################
LIST_BASE_PATHS = [ "/scratch/jh2/nk7952" ]
BOOL_DEBUG = 1

## subset of simulations
LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm3000" ]
LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
LIST_RES_FOLDERS   = [ ]


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def createSubFolders(filepath):
  dict_sim_inputs = FlashData.readSimInputs(filepath.replace("576", "288"), bool_verbose=False)
  Mach = dict_sim_inputs["desired_Mach"]
  Re = dict_sim_inputs["Re"]
  Rm = dict_sim_inputs["Rm"]
  Pm = dict_sim_inputs["Pm"]
  WWFnF.createDirectory(filepath)


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  if BOOL_DEBUG: print("Running in debug mode.")
  [
    createSubFolders(
      WWFnF.createFilepath([ base_path, suite_folder, mach_folder, sim_folder, res_folder ])
    )
    for base_path    in LIST_BASE_PATHS
    for suite_folder in LIST_SUITE_FOLDERS
    for mach_folder  in LIST_MACH_FOLDERS
    for sim_folder   in LIST_SIM_FOLDERS
    for res_folder   in LIST_RES_FOLDERS
    if WWFnF.checkDirectoryExists(
      WWFnF.createFilepath([ base_path, suite_folder, mach_folder, sim_folder ])
    ) and not(WWFnF.checkDirectoryExists(
      WWFnF.createFilepath([ base_path, suite_folder, mach_folder, sim_folder, res_folder ])
    ))
  ]


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM