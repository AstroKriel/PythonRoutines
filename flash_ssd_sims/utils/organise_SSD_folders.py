## ###############################################################
## MODULES
## ###############################################################
import sys
import numpy as np

## load user defined modules
from Loki.TheUsefulModule import WWFnF, WWTerminal
from Loki.TheFlashModule import FileNames, FlashData, JobProcessFiles


## ###############################################################
## PROGRAM PARAMTERS
## ###############################################################
BOOL_DEBUG_MODE  = 0
BOOL_SAFE_MODE   = 0
BOOL_IGNORE_JOBS = 1

BOOL_REMOVE_CLUTTER       = 0
BOOL_ORGANISE_PLT_FILES   = 0
BOOL_ORGANISE_SPECT_FILES = 0
BOOL_REDUCE_NUMBER_FILES  = 0
BOOL_AGGRESSIVE           = 0
BOOL_PROCESS_PLT_FILES    = 1

# ## full list of ek9 simulations
# LIST_BASE_PATHS    = [ "/scratch/ek9/nk7952/" ]
# LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
# LIST_RES_FOLDERS   = [ "576" ]
# LIST_SIM_NAMES     = [ ]

# ## full list of jh2 simulations
# LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/" ]
# LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
# LIST_RES_FOLDERS   = [ "18", "36", "72", "144", "288", "576", "1152" ]
# LIST_SIM_NAMES     = [ ]

## new version of simulations
LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/" ]
LIST_SUITE_FOLDERS = [ "Re500" ]
LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach0.5", "Mach1", "Mach2", "Mach5", "Mach10" ]
LIST_SIM_FOLDERS   = [ "Pm1", "Pm5" ]
LIST_RES_FOLDERS   = [ "288" ]
# LIST_RES_FOLDERS   = [
#   "288"
#   if (v_index == 1) else
#   f"288v{v_index}"
#   for v_index in range(1, 10)
# ]
LIST_SIM_NAMES     = [ ]


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def _runCommand(command, directory=None):
  WWTerminal.runCommand(command, directory, BOOL_DEBUG_MODE)

def deleteMassFiles(directory, filename_starts_with="", filename_ends_with=""):
  list_files_in_directory = WWFnF.getFilesInDirectory(
    directory            = directory,
    filename_starts_with = filename_starts_with,
    filename_ends_with   = filename_ends_with
  )
  if len(list_files_in_directory) == 0: return
  _runCommand(f"rm {directory}/{filename_starts_with}*{filename_ends_with}")
  print(f"\t> delete(): {str(len(list_files_in_directory)).zfill(4)} '{filename_starts_with}*{filename_ends_with}' files in: {directory}")

def deleteSpecificFiles(
    directory,
    filename_starts_with  = "",
    filename_ends_with    = "",
    filename_not_contains = "",
    delete_from           = 0,
    delete_to             = None,
    delete_every_nth      = 1
  ):
  list_files_in_directory = WWFnF.getFilesInDirectory(
    directory             = directory,
    filename_starts_with  = None if (filename_starts_with  == "") else filename_starts_with,
    filename_ends_with    = None if (filename_ends_with    == "") else filename_ends_with,
    filename_not_contains = None if (filename_not_contains == "") else filename_not_contains
  )
  if len(list_files_in_directory) == 0: return
  list_files_safe_to_delete = list_files_in_directory[:-5] if BOOL_SAFE_MODE else list_files_in_directory
  if delete_to is None:
    list_filenumbers = [
      int(filename.replace(filename_starts_with, "").replace(filename_ends_with, ""))
      for filename in list_files_safe_to_delete
    ]
    if len(list_filenumbers) == 0: return
    delete_to = max(list_filenumbers)
  num_files_deleted = 0
  for file_index in range(delete_from, delete_to, delete_every_nth):
    filename = filename_starts_with + str(int(file_index)).zfill(4)
    if filename_ends_with != "": filename += filename_ends_with
    if filename in list_files_safe_to_delete:
      _runCommand(f"rm {directory}/{filename}")
      num_files_deleted += 1
  if num_files_deleted == 0: return
  print(f"\t> delete(start={str(delete_from).zfill(4)}, to={str(delete_to).zfill(4)}, step={str(delete_every_nth).zfill(4)}, exclude='{filename_not_contains}'): {str(num_files_deleted).zfill(4)} of {str(len(list_files_in_directory)).zfill(4)} '{filename_starts_with}*{filename_ends_with}' files meets condition in: {directory}")

def moveFiles(
    directory_from, directory_to,
    filename_contains     = None,
    filename_not_contains = None
  ):
  list_files_in_directory= WWFnF.getFilesInDirectory(
    directory             = directory_from,
    filename_starts_with  = "Turb",
    filename_contains     = filename_contains,
    filename_not_contains = filename_not_contains
  )
  if len(list_files_in_directory) == 0: return
  _runCommand(f"mv {directory_from}/*{filename_contains}* {directory_to}/.")
  str_condition = f" (exclude '{filename_not_contains}')" if (filename_not_contains is not None) else ""
  print(f"\t> move(): {str(len(list_files_in_directory)).zfill(4)} '*{filename_contains}*' files{str_condition}")
  print("\t\tFrom:", directory_from)
  print("\t\tTo:", directory_to)

def countFiles(
    directory,
    filename_contains     = None,
    filename_not_contains = None,
    bool_verbose          = False
  ):
  list_files_in_directory= WWFnF.getFilesInDirectory(
    directory             = directory,
    filename_starts_with  = "Turb",
    filename_contains     = filename_contains,
    filename_not_contains = filename_not_contains
  )
  num_files = len(list_files_in_directory)
  if bool_verbose: print(f"\t> There are {str(num_files).zfill(4)} '*{filename_contains}*' files in: {directory}")
  return num_files, list_files_in_directory

def renameFiles(directory, old_phrase, new_phrase):
  list_files_in_directory= WWFnF.getFilesInDirectory(
    directory         = directory,
    filename_contains = old_phrase
  )
  if len(list_files_in_directory) == 0: return
  command_arg = "-n" if BOOL_DEBUG_MODE else ""
  _runCommand(f"rename {command_arg} {old_phrase} {new_phrase} *", directory)
  print(f"\t> rename(): {str(len(list_files_in_directory)).zfill(4)} '*{old_phrase}*' file(s) to '*{new_phrase}*'")


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class OrganiseSimFolder():
  def __init__(self, directory_sim):
    self.directory_sim    = directory_sim
    self.directory_plt    = WWFnF.createFilepath([directory_sim, "plt"])
    self.directory_spect  = WWFnF.createFilepath([directory_sim, "spect"])
    self.dict_sim_inputs = FlashData.readSimInputs(self.directory_sim, bool_verbose=False)
    WWFnF.createDirectory(self.directory_plt,   bool_verbose=False)
    WWFnF.createDirectory(self.directory_spect, bool_verbose=False)

  def performRourtine(self):
    self.bool_submit_job = False
    self.sim_name = FlashData.getSimName(self.dict_sim_inputs)
    if len(LIST_SIM_NAMES) > 0:
      if not(self.sim_name in LIST_SIM_NAMES): return
    print("Organising:", self.directory_sim)
    if BOOL_DEBUG_MODE: print("Running in debug mode.")
    if BOOL_SAFE_MODE:  print("Running in safe mode.")
    bool_sim_job_running = WWFnF.checkIfJobIsRunning(self.directory_sim, FileNames.FILENAME_RUN_SIM_JOB)
    bool_plt_job_running = WWFnF.checkIfJobIsRunning(self.directory_plt, FileNames.FILENAME_PROCESS_PLT_JOB)
    if any([ bool_sim_job_running, bool_plt_job_running ]) and not(BOOL_IGNORE_JOBS):
      print("\t> A job is currently running\n")
      return
    if BOOL_REMOVE_CLUTTER:       self._removeExtraFiles()
    if BOOL_ORGANISE_PLT_FILES:   self._organisePltFiles()
    if BOOL_ORGANISE_SPECT_FILES: self._organiseSpectFiles()
    if BOOL_REDUCE_NUMBER_FILES:  self._reduceNumberOfFiles()
    if BOOL_PROCESS_PLT_FILES:    self._checkNumUnprocessedPltFiles()
    print(" ")

  def _removeExtraFiles(self):
    print("Removing extraneous files...")
    ## remove extraneous files
    deleteMassFiles(self.directory_sim, filename_starts_with="core.flash4_")
    deleteMassFiles(self.directory_sim, filename_starts_with="Turb_proj_")
    deleteMassFiles(self.directory_sim, filename_starts_with="Turb_slice_")
    # for filepath in [ self.directory_sim, self.directory_plt, self.directory_spect ]:
    #   deleteMassFiles(filepath, filename_ends_with="_mags.dat")
    #   deleteMassFiles(filepath, filename_ends_with="_vels.dat")
    #   deleteMassFiles(filepath, filename_ends_with="_sqrtrho.dat")

  def _organisePltFiles(self):
    print("Organising plt-files...")
    if not WWFnF.checkDirectoryExists(self.directory_plt): raise Exception("Error: 'plt' sub-folder does not exist")
    dict_plt_file_deets = {
      "filename_contains"     : "plt_",
      "filename_not_contains" : "spect_"
    }
    moveFiles(self.directory_sim, self.directory_plt, **dict_plt_file_deets)
    countFiles(self.directory_sim, **dict_plt_file_deets)
    countFiles(self.directory_plt, **dict_plt_file_deets)
    countFiles(self.directory_spect, **dict_plt_file_deets)

  def _organiseSpectFiles(self):
    print("Organising spect-files...")
    if not WWFnF.checkDirectoryExists(self.directory_spect): raise Exception("Error: 'spect' sub-folder does not exist")
    ## check that there are spectra files to move
    self.num_spect_files_in_plt, _ = countFiles(
      directory         = self.directory_plt,
      filename_contains = "spect_"
    )
    if self.num_spect_files_in_plt == 0: return
    ## move spectra from the simulation folder to spect sub-folder
    moveFiles(
      directory_from    = self.directory_sim,
      directory_to      = self.directory_spect,
      filename_contains = "spect_"
    )
    ## move spectra from plt sub-folder to spect sub-folder
    moveFiles(
      directory_from    = self.directory_plt,
      directory_to      = self.directory_spect,
      filename_contains = "spect_"
    )
    ## count number of spectra in the spect sub-folder
    countFiles(self.directory_sim,   filename_contains="spect_")
    countFiles(self.directory_plt,   filename_contains="spect_")
    countFiles(self.directory_spect, filename_contains="spect_")
    # ## rename current spectra files
    # renameFiles(
    #   directory  = self.directory_spect,
    #   old_phrase = "dset_curx_cury_curz",
    #   new_phrase = "current"
    # )

  def _reduceNumberOfFiles(self):
    print("Reducing dataset (number of chk-, plt-, and spect-files)...")
    list_chk_files = WWFnF.getFilesInDirectory(
      directory            = self.directory_sim,
      filename_starts_with = "Turb_hdf5_chk_"
    )
    ## if there are too many chk-files
    num_chk_files_to_keep = 2 if BOOL_SAFE_MODE else 1
    num_chk_files_removed = 0
    outputs_per_t_turb = self.dict_sim_inputs["outputs_per_t_turb"]
    t_turb_from = 5*outputs_per_t_turb + 1
    if len(list_chk_files) > num_chk_files_to_keep:
      for file_index in range(len(list_chk_files) - num_chk_files_to_keep):
        _runCommand(f"rm {self.directory_sim}/{list_chk_files[file_index]}")
        num_chk_files_removed += 1
      print(f"\t> Removed {num_chk_files_removed} (+ keeping {num_chk_files_to_keep}) chk-files from: {self.directory_sim}")
    for directory in [
        self.directory_sim,
        self.directory_plt,
        self.directory_spect
      ]:
      dict_transient_deets = {
        "directory"            : directory,
        "filename_starts_with" : "Turb_hdf5_plt_cnt_",
        "delete_from"          : 0,
        "delete_to"            : t_turb_from, # data before 5 t/t_turb
        "delete_every_nth"     : 1,
      }
      deleteSpecificFiles(filename_not_contains="spect", **dict_transient_deets)
      deleteSpecificFiles(filename_ends_with="_spect_magnetic.dat", **dict_transient_deets)
      deleteSpecificFiles(filename_ends_with="_spect_kinetic.dat", **dict_transient_deets)
      deleteSpecificFiles(filename_ends_with="_spect_current.dat", **dict_transient_deets)
      dict_subset_deets_conservative = {
        "directory"            : directory,
        "filename_starts_with" : "Turb_hdf5_plt_cnt_",
        "delete_from"          : t_turb_from,
        "delete_every_nth"     : 2,
      }
      deleteSpecificFiles(filename_not_contains="spect", **dict_subset_deets_conservative)
      deleteSpecificFiles(filename_ends_with="_spect_magnetic.dat", **dict_subset_deets_conservative)
      deleteSpecificFiles(filename_ends_with="_spect_kinetic.dat", **dict_subset_deets_conservative)
      deleteSpecificFiles(filename_ends_with="_spect_current.dat", **dict_subset_deets_conservative)
      if BOOL_AGGRESSIVE:
        dict_subset_deets_aggressive = {
          "directory"            : directory,
          "filename_starts_with" : "Turb_hdf5_plt_cnt_",
          "delete_from"          : t_turb_from+3,
          "delete_every_nth"     : 4,
        }
        deleteSpecificFiles(filename_not_contains="spect", **dict_subset_deets_aggressive)
        deleteSpecificFiles(filename_ends_with="_spect_magnetic.dat", **dict_subset_deets_aggressive)
        deleteSpecificFiles(filename_ends_with="_spect_kinetic.dat", **dict_subset_deets_aggressive)
        deleteSpecificFiles(filename_ends_with="_spect_current.dat", **dict_subset_deets_aggressive)

  def _checkNumUnprocessedPltFiles(self):
    print("Checking the number of unprocessed plt-files...")
    self.num_files_in_plt_folder, self.list_files_in_plt = countFiles(
        directory             = self.directory_plt,
        filename_contains     = "plt_",
        filename_not_contains = "spect_",
        bool_verbose          = False
      )
    file_start_index = np.nan
    for spect_field in [ "_kin", "_mag", "_cur" ]:
      num_files_in_spect_folder, list_files_in_spect = countFiles(
        directory         = self.directory_spect,
        filename_contains = spect_field,
        bool_verbose      = False
      )
      if num_files_in_spect_folder < self.num_files_in_plt_folder:
        print(f"\t> {str(num_files_in_spect_folder).zfill(4)} '{spect_field}' spect-files of {str(self.num_files_in_plt_folder).zfill(4)} plt-files have been processed and moved ({str(self.num_files_in_plt_folder - num_files_in_spect_folder).zfill(4)} missing)")
        self.bool_submit_job = True
        if num_files_in_spect_folder > 0:
          list_spect_subfilenames = [
            filename.split("_spect")[0]
            for filename in list_files_in_spect
          ]
          list_files_unprocessed = [
            int(filename.split("_")[-1]) # filename: Turb_hdf5_plt_cnt_NUMBER
            if filename not in list_spect_subfilenames else np.nan
            for filename in self.list_files_in_plt
          ]
          min_file_indices = np.nanmin(list_files_unprocessed)
          file_start_index = np.nanmin([ file_start_index, min_file_indices ])
    if self.bool_submit_job:
      if BOOL_DEBUG_MODE: return
      if np.isnan(file_start_index): file_start_index = 0
      JobProcessFiles.JobProcessFiles(
        directory_plt        = self.directory_plt,
        dict_sim_inputs     = self.dict_sim_inputs,
        list_spect_datasets = [ "kin", "mag", "cur" ],
        file_start_index    = int(file_start_index)
      )
      WWTerminal.submitJob(self.directory_plt, FileNames.FILENAME_PROCESS_PLT_JOB)


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
  list_submitted_jobs = []
  for directory_sim in list_directory_sims:
    obj_sim_folder = OrganiseSimFolder(directory_sim)
    obj_sim_folder.performRourtine()
    if obj_sim_folder.bool_submit_job: list_submitted_jobs.append(directory_sim)
  if len(list_submitted_jobs) > 0:
    print("Jobs have been submitted in the following simulation diectories:")
    print("\t> " + "\n\t> ".join(list_submitted_jobs))


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM