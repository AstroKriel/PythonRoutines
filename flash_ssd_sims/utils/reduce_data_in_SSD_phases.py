## ###############################################################
## MODULES
## ###############################################################
import sys
import numpy as np

## load user defined modules
from TheUsefulModule import WWFnF, WWTerminal
from TheFlashModule import FileNames, FlashData


## ###############################################################
## PROGRAM PARAMTERS
## ###############################################################
BOOL_DEBUG_MODE = 1

LIST_BASE_PATHS = [ "/scratch/jh2/nk7952/" ]
LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm3000" ]
LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
LIST_RES_FOLDERS   = [ "18", "36", "72", "144", "288", "576" ]


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def _runCommand(command, directory=None):
  WWTerminal.runCommand(command, directory, BOOL_DEBUG_MODE)

def deleteSpecificFiles(
    directory, num_files_to_keep,
    filename_starts_with  = "",
    filename_ends_with    = "",
    filename_not_contains = "",
    delete_from           = 0,
    delete_to             = None
  ):
  list_files_in_time_range = WWFnF.getFilesInDirectory(
    directory             = directory,
    loc_file_index        = 4,
    file_start_index      = delete_from,
    file_end_index        = np.inf if delete_to is None else delete_to,
    filename_starts_with  = None if (filename_starts_with  == "") else filename_starts_with,
    filename_ends_with    = None if (filename_ends_with    == "") else filename_ends_with,
    filename_not_contains = None if (filename_not_contains == "") else filename_not_contains
  )
  if len(list_files_in_time_range) == 0: return
  if delete_to is None:
    delete_to = max([
      int(filename.split("_")[4])
      for filename in list_files_in_time_range
    ])
  index_step = len(list_files_in_time_range) // num_files_to_keep
  num_files_deleted = 0
  for file_index in range(len(list_files_in_time_range)):
    filename = list_files_in_time_range[file_index]
    if file_index % index_step == 0: continue
    _runCommand(f"rm {directory}/{filename}")
    num_files_deleted += 1
  if num_files_deleted == 0: return
  print(f"\t> delete(start={str(delete_from).zfill(4)}, to={str(delete_to).zfill(4)}, keep={str(num_files_to_keep).zfill(4)}, step={str(index_step)}, exclude='{filename_not_contains}'): {str(num_files_deleted).zfill(4)} of {str(len(list_files_in_time_range)).zfill(4)} ({str(len(list_files_in_time_range) - num_files_deleted).zfill(4)} renmain) '{filename_starts_with}*{filename_ends_with}' files meets condition in: {directory}")

def countFiles(
    directory, filename_starts_with,
    filename_contains     = None,
    filename_not_contains = None,
    bool_verbose          = False
  ):
  list_files_in_directory= WWFnF.getFilesInDirectory(
    directory             = directory,
    filename_starts_with  = filename_starts_with,
    filename_contains     = filename_contains,
    filename_not_contains = filename_not_contains
  )
  num_files = len(list_files_in_directory)
  if bool_verbose: print(f"\t> There are {str(num_files).zfill(4)} '*{filename_contains}*' files in: {directory}")
  return num_files, list_files_in_directory


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class ReorganiseSimFolder():
  def __init__(self, directory_sim):
    self.directory_sim    = directory_sim
    self.directory_plt    = WWFnF.createFilepath([directory_sim, "plt"])
    self.directory_spect  = WWFnF.createFilepath([directory_sim, "spect"])
    self.dict_sim_inputs = FlashData.readSimInputs(self.directory_sim, bool_verbose=False)
    try:
      dict_sim_summary = FlashData.readSimSummary(self.directory_sim, bool_verbose=False)
      self.outputs_per_t_turb = dict_sim_summary["outputs_per_t_turb"]
      self.time_linear_start  = dict_sim_summary["linear_regime"]["start_time"]
      self.time_linear_end    = dict_sim_summary["linear_regime"]["end_time"]
      self.bool_regimes_defined = True
    except: self.bool_regimes_defined = False

  def performRourtine(self):
    if not(self.bool_regimes_defined):
      print("\t> SSD regimes have not been defined/measured for this simulation")
      return
    bool_sim_job_running = WWFnF.checkIfJobIsRunning(self.directory_sim, FileNames.FILENAME_RUN_SIM_JOB)
    bool_plt_job_running = WWFnF.checkIfJobIsRunning(self.directory_plt, FileNames.FILENAME_PROCESS_PLT_JOB)
    if any([ bool_sim_job_running, bool_plt_job_running ]):
      print("\t> A job is currently running")
      return
    if self._checkIfAnyFilestNeedToBeMoved(): return
    self._reduceNumberOfFiles()

  def _checkIfAnyFilestNeedToBeMoved(self):
    count_plt_in_sim_folder,   _ = countFiles(self.directory_sim, filename_starts_with="Turb_hdf5_plt_cnt_", filename_not_contains="specr")
    count_spect_in_plt_folder, _ = countFiles(self.directory_plt, filename_starts_with="Turb_hdf5_plt_cnt_", filename_contains="spect")
    if count_plt_in_sim_folder   > 0: print(f"\t> There are {count_plt_in_sim_folder} plt-files that need to be moved from the sim- to plt-folder")
    if count_spect_in_plt_folder > 0: print(f"\t> There are {count_spect_in_plt_folder} spect-files that need to be moved from the plt- to spect-folder")
    return (count_plt_in_sim_folder + count_spect_in_plt_folder) > 0

  def _reduceNumberOfFiles(self):
    print("Reducing dataset (number of plt- and spect-files)...")
    print("\t> Kinematic phase...")
    dict_exp_deets = {
      "filename_starts_with" : "Turb_hdf5_plt_cnt_",
      "delete_from"          : round(self.outputs_per_t_turb * 5),
      "delete_to"            : round(self.outputs_per_t_turb * self.time_linear_start),
      "num_files_to_keep"    : 40
    }
    deleteSpecificFiles(directory=self.directory_plt,   filename_not_contains="spect", **dict_exp_deets)
    deleteSpecificFiles(directory=self.directory_spect, filename_ends_with="_spect_magnetic.dat", **dict_exp_deets)
    deleteSpecificFiles(directory=self.directory_spect, filename_ends_with="_spect_kinetic.dat",  **dict_exp_deets)
    deleteSpecificFiles(directory=self.directory_spect, filename_ends_with="_spect_current.dat",  **dict_exp_deets)
    print("\t> Saturated phase...")
    dict_sat_deets = {
      "filename_starts_with" : "Turb_hdf5_plt_cnt_",
      "delete_from"          : round(self.outputs_per_t_turb * self.time_linear_end),
      "num_files_to_keep"    : 40
    }
    deleteSpecificFiles(directory=self.directory_plt,   filename_not_contains="spect", **dict_sat_deets)
    deleteSpecificFiles(directory=self.directory_spect, filename_ends_with="_spect_magnetic.dat", **dict_sat_deets)
    deleteSpecificFiles(directory=self.directory_spect, filename_ends_with="_spect_kinetic.dat",  **dict_sat_deets)
    deleteSpecificFiles(directory=self.directory_spect, filename_ends_with="_spect_current.dat",  **dict_sat_deets)


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
    print("Reorganising:", directory_sim)
    if BOOL_DEBUG_MODE: print("Running in debug mode.")
    obj_sim_folder = ReorganiseSimFolder(directory_sim)
    obj_sim_folder.performRourtine()
    print(" ")


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM