#!/bin/env python3


## ###############################################################
## MODULES
## ###############################################################
import sys

## load user defined modules
from TheFlashModule import FileNames, FlashData, JobRunSim
from TheUsefulModule import WWTerminal, WWFnF, WWObjs


## ###############################################################
## PROGRAM PARAMTERS
## ###############################################################
BOOL_DEBUG_MODE  = 1

LIST_BASE_PATHS    = [ "/scratch/ek9/nk7952/" ]
LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
LIST_RES_FOLDERS   = [ "576" ]

LIST_SIM_NAMES     = [ ]


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def _runCommand(command, directory=None):
  WWTerminal.runCommand(command, directory)

def deleteMassFiles(
    directory,
    filename_starts_with = "",
    filename_contains    = "",
    filename_ends_with   = "",
  ):
  list_files_in_directory = WWFnF.getFilesInDirectory(
    directory            = directory,
    filename_starts_with = filename_starts_with,
    filename_contains    = filename_contains,
    filename_ends_with   = filename_ends_with,
  )
  if len(list_files_in_directory) == 0: return
  str_condition = f"{filename_starts_with}*{filename_contains}*{filename_ends_with}"
  str_condition = str_condition.replace("**", "*")
  _runCommand(f"rm {directory}/{str_condition}")
  print(f"\t> delete(): {str(len(list_files_in_directory)).zfill(4)} '{str_condition}' files in: {directory}")

def deleteFile(directory, filename):
  if not WWFnF.checkFileExists(directory, filename): return
  _runCommand(f"rm {directory}/{filename}")
  print(f"\t> delete(): file '{filename}' in: {directory}")

def deleteFilesInFolder(directory):
  list_files_in_directory = WWFnF.getFilesInDirectory(directory=directory)
  if len(list_files_in_directory) == 0: return
  _runCommand(f"rm {directory}/*")
  print(f"\t> delete(): {str(len(list_files_in_directory)).zfill(4)} files in: {directory}")


## ###############################################################
## OPPERATOR CLASS
## ###############################################################
class RestartSim:
  def __init__(self, directory_sim):
    self.directory_sim = directory_sim

  def performRoutine(self):
    print("Looking at:", self.directory_sim)
    if WWFnF.checkIfJobIsRunning(self.directory_sim, FileNames.FILENAME_RUN_SIM_JOB):
      print("\t> Simulation is currently running")
      return
    if BOOL_DEBUG_MODE: return
    ## delete data
    deleteMassFiles(self.directory_sim, filename_starts_with="Turb")
    deleteMassFiles(self.directory_sim, filename_starts_with="job_")
    deleteMassFiles(self.directory_sim, filename_contains="_backup")
    deleteMassFiles(self.directory_sim, filename_contains=".o")
    deleteMassFiles(self.directory_sim, filename_ends_with=".sh")
    deleteFile(self.directory_sim, "sim_outputs.h5")
    deleteFile(self.directory_sim, "sim_summary.json")
    deleteFile(self.directory_sim, "stir.dat")
    for directory in [
        f"{self.directory_sim}/plt",
        f"{self.directory_sim}/spect",
        f"{self.directory_sim}/vis_folder",
      ]:
      deleteFilesInFolder(directory)
    ## update inputs file
    self.dict_sim_inputs = FlashData.readSimInputs(self.directory_sim)
    self.dict_sim_inputs["run_index"] = 0
    self.dict_sim_inputs["bool_driving_tuned"] = True
    self.dict_sim_inputs["outputs_per_t_turb"] = 4
    WWObjs.saveDict2JsonFile(f"{self.directory_sim}/{FileNames.FILENAME_SIM_INPUTS}", self.dict_sim_inputs)
    ## create a new flash parameter file
    obj_prep_sim = JobRunSim.JobRunSim(
      directory_sim   = self.directory_sim,
      dict_sim_inputs = self.dict_sim_inputs
    )
    obj_prep_sim.prepForRestartFromScratch()
    ## submit simulation if it needs to run for longer
    WWTerminal.submitJob(self.directory_sim, FileNames.FILENAME_RUN_SIM_JOB)


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  list_directory_sims = FlashData.getListOfSimDirectories(
    list_base_paths    = LIST_BASE_PATHS,
    list_suite_folders = LIST_SUITE_FOLDERS,
    list_mach_folders  = LIST_MACH_FOLDERS,
    list_sim_folders   = LIST_SIM_FOLDERS,
    list_res_folders   = LIST_RES_FOLDERS
  )
  for directory_sim in list_directory_sims:
    RestartSimObj = RestartSim(directory_sim)
    RestartSimObj.performRoutine()
    print(" ")


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM