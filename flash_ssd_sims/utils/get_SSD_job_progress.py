#!/usr/bin/env python3

## ###############################################################
## MODULES
## ###############################################################
import sys
import numpy as np

from datetime import datetime

## load user defined modules
from TheFlashModule import FileNames, FlashData, LoadData
from TheUsefulModule import WWFnF


## ###############################################################
## PROGRAM PARAMETERS
## ###############################################################
LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/" ]
LIST_SUITE_FOLDERS = [ "Re500" ]
LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach0.5", "Mach1", "Mach2", "Mach5", "Mach10" ]
LIST_SIM_FOLDERS   = [ "Pm1" ]
# LIST_RES_FOLDERS   = [ "288" ]
LIST_RES_FOLDERS   = [
  "288"
  if (v_index == 1) else
  f"288v{v_index}"
  for v_index in range(1, 11)
]
LIST_SIM_NAMES     = [ ]


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class CheckSimProgress():
  def __init__(self, directory_sim):
    self.directory_sim = directory_sim
    print("Checking simulation:", self.directory_sim)
    self.bool_sim_defined = WWFnF.checkFileExists(self.directory_sim, FileNames.FILENAME_SIM_INPUTS)
    if not(self.bool_sim_defined):
      print(f"\t> Simulation is undefined: {self.directory_sim}\n")
      return
    dict_sim_inputs   = FlashData.readSimInputs(self.directory_sim, bool_verbose=False)
    self.sim_name     = FlashData.getSimName(dict_sim_inputs)
    self.t_turb       = dict_sim_inputs["t_turb"]
    self.t_end        = dict_sim_inputs["max_num_t_turb"]
    self.desired_Mach = dict_sim_inputs["desired_Mach"]

  def performRoutine(self):
    if not(self.bool_sim_defined): return
    if len(LIST_SIM_NAMES) > 0:
      if not(self.sim_name in LIST_SIM_NAMES): return
    if not WWFnF.checkFileExists(self.directory_sim, FileNames.FILENAME_FLASH_VI_DATA):
      print("\t> Simulation has not been run yet.\n")
      return
    print(f"Check figure: {self.directory_sim}/vis_folder/{self.sim_name}_time_evolution.png")
    bool_sufficient_data_exists = self._loadData()
    if bool_sufficient_data_exists:
      self._measureMach()
      self._magneticGrowth()
    print(" ")
    
  def __round(self, value):
    return round(value, 3)

  def _loadData(self):
    bool_sufficient_data_exists = False
    ## load Mach data
    data_time, self.data_Mach = LoadData.loadVIData(
      directory  = self.directory_sim,
      field_name = "mach",
      t_turb     = self.t_turb,
      time_start = 2.0,
      time_end   = np.inf
    )
    ## load magnetic energy
    _, self.data_mag_energy = LoadData.loadVIData(
      directory  = self.directory_sim,
      field_name = "mag",
      t_turb     = self.t_turb,
      time_start = 2.0,
      time_end   = np.inf
    )
    if len(data_time) > 100:
      bool_sufficient_data_exists = True
      t_duration = self.__round(data_time[-1])
      percent_done = 100 * t_duration / self.t_end
      print(f"\t> Progressed to {t_duration} t/t_turb")
      if percent_done < 98.0:
        print(f"\t> {percent_done:.2f}% of desired {self.t_end} t/t_turb")
        if WWFnF.checkIfJobIsRunning(self.directory_sim, FileNames.FILENAME_RUN_SIM_JOB):
          print(f"\t> Simulation is still running!")
        else: print(f"\t> Simulation needs to be run to completion.")
      else: print("\t> Simulation has finished.")
    else: print("\t> Simulation hasn't run long enough.")
    return bool_sufficient_data_exists

  def _measureMach(self):
    ## measure Mach number statistics in kinematic phase
    ave_Mach = self.__round(np.mean(self.data_Mach))
    std_Mach = self.__round(np.std(self.data_Mach))
    print(f"\t> Desired Mach = {self.desired_Mach}")
    print(f"\t> Measured Mach = {ave_Mach} +/- {std_Mach}")

  def _magneticGrowth(self):
    ## measure magnetic energy growth
    mag_growth = self.__round(np.log(np.max(self.data_mag_energy)) - np.log(np.min(self.data_mag_energy)))
    print(f"\t> Magnetic energy ln-growth = {mag_growth}")


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  print("Checking at:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "\n")
  list_directory_sims = FlashData.getListOfSimDirectories(
    list_base_paths    = LIST_BASE_PATHS,
    list_suite_folders = LIST_SUITE_FOLDERS,
    list_mach_folders  = LIST_MACH_FOLDERS,
    list_sim_folders   = LIST_SIM_FOLDERS,
    list_res_folders   = LIST_RES_FOLDERS
  )
  for directory_sim in list_directory_sims:
    obj_tune_driving = CheckSimProgress(directory_sim)
    obj_tune_driving.performRoutine()


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM