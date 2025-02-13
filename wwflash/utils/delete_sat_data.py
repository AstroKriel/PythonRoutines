#!/usr/bin/env python3

## ###############################################################
## MODULES
## ###############################################################
import os, sys, random
import numpy as np

## 'tmpfile' needs to be loaded before any 'matplotlib' libraries,
## so matplotlib stores its cache in a temporary directory.
## (necessary when plotting in parallel)
import tempfile
os.environ["MPLCONFIGDIR"] = tempfile.mkdtemp()
import matplotlib.pyplot as plt

## load user defined modules
from TheFlashModule import FlashData, FileNames, LoadData
from TheUsefulModule import WWFnF, WWLists
from TheFittingModule import FitFuncs


## ###############################################################
## PROGRAM PARAMETERS
## ###############################################################
PATH_SCRATCH = "/scratch/jh2/nk7952/"

## PLASMA PARAMETER SET
LIST_SUITE_FOLDERS = [  ]
LIST_MACH_FOLDERS  = [  ]
LIST_SIM_FOLDERS   = [  ]
LIST_RES_FOLDERS   = [  ]


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class RestartSim():
  def __init__(self, directory_sim):
    self.directory_sim = directory_sim
    self.directory_vis     = f"{directory_sim}/vis_folder/"
    WWFnF.createDirectory(self.directory_vis, bool_verbose=False)
    self.dict_sim_inputs  = FlashData.readSimInputs(self.directory_sim, False)
    self.max_num_t_turb   = self.dict_sim_inputs["max_num_t_turb"]
    self.t_turb           = self.dict_sim_inputs["t_turb"]
    self.growth_rate_tol  = 5e-2
  
  def performRoutine(self):
    self._readLastFileIndex()
    self._checkEmagSaturated()

  def _readLastFileIndex(self):
    ## define helper function
    def getLastFileIndex(filename_starts_with, sub_folder=""):
      list_filenames = WWFnF.getFilesInDirectory(
        directory             = f"{self.directory_sim}/{sub_folder}/",
        filename_starts_with  = filename_starts_with,
        filename_not_contains = "spect",
        loc_file_index        = -1,
      )
      if len(list_filenames) == 0: return np.nan
      last_index = max([
        int(filename.split("_")[-1])
        for filename in list_filenames
      ])
      return last_index
    ## get last output file indices
    self.last_chk_index = getLastFileIndex(FileNames.FILENAME_FLASH_CHK_FILES)
    last_plt_index_sim  = getLastFileIndex(FileNames.FILENAME_FLASH_PLT_FILES)
    last_plt_index_plt  = getLastFileIndex(FileNames.FILENAME_FLASH_PLT_FILES, sub_folder="plt")
    self.last_plt_index = int(np.nanmax([
      last_plt_index_sim,
      last_plt_index_plt
    ]))
    ## get latest simulation job index
    list_sim_outputs = [
      int(file.split(".out")[1])
      if len(file.split(".out")) > 1 else
      np.nan
      for file in os.listdir(self.directory_sim)
      if file.startswith(FileNames.FILENAME_RUN_SIM_OUTPUT)
    ]
    if len(list_sim_outputs) > 0:
      self.last_run_index = np.nanmax(list_sim_outputs)
    else: self.last_run_index = 0

  def _checkEmagSaturated(self):
    self.data_time, data_Emag = LoadData.loadVIData(
      directory  = self.directory_sim,
      field_name = "mag",
      t_turb     = self.t_turb,
      time_start = 2.0,
      time_end   = np.inf
    )
    ## determine if Emag has saturated
    time_grouped        = []
    growth_rate_grouped = []
    fig, axs = plt.subplots(nrows=2, figsize=(6, 2*4), sharex=True)
    for time_start_fit in sorted([ random.uniform(5, max(self.data_time))-10 for _ in range(50) ]):
      index_start_fit = WWLists.getIndexClosestValue(self.data_time, time_start_fit)
      index_end_fit   = -2
      time_start_fit  = self.data_time[index_start_fit]
      time_end_fit    = self.data_time[index_end_fit]
      ## fit linear model in log-linear space
      growth_rate, _ = FitFuncs.fitExpFunc(
        data_x            = self.data_time,
        data_y            = data_Emag,
        index_start_fit   = index_start_fit,
        index_end_fit     = index_end_fit,
        num_interp_points = 10 # * (time_end_fit - time_start_fit),
      )
      ## measure variation
      time_grouped.append(time_start_fit)
      growth_rate_grouped.append(abs(growth_rate))
    ## plot data to check
    axs[0].plot(self.data_time, data_Emag, color="black", ls="-")
    axs[1].plot(time_grouped, growth_rate_grouped, color="green", marker="o", ls="-")
    ## label axis
    axs[0].set_yscale("log")
    axs[1].set_yscale("log")
    axs[0].set_ylabel(r"$E_{\rm mag}$")
    axs[1].set_ylabel(r"$|\Gamma|$")
    axs[1].set_xlabel(r"$t / t_{\rm turb}$")
    axs[1].axhline(y=self.growth_rate_tol, ls=":", lw=2, color="black")
    ## save figure
    print("Saving figure...")
    fig_name     = f"Emag_check.png"
    filepath_fig = f"{self.directory_vis}/{fig_name}"
    fig.savefig(filepath_fig, dpi=75)
    plt.close(fig)
    print("Saved figure:", filepath_fig)
    print(" ")


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  list_directory_sims = FlashData.getListOfSimDirectories(
    list_base_paths    = [ PATH_SCRATCH ],
    list_suite_folders = LIST_SUITE_FOLDERS,
    list_mach_folders  = LIST_MACH_FOLDERS,
    list_sim_folders   = LIST_SIM_FOLDERS,
    list_res_folders   = LIST_RES_FOLDERS
  )
  for sim_filepath in list_directory_sims:
    print("Looking at:", sim_filepath)
    obj_tune_driving = RestartSim(sim_filepath)
    obj_tune_driving.performRoutine()
    print(" ")


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM