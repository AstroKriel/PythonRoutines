## ###############################################################
## MODULES
## ###############################################################
import os, sys
import numpy as np

## load user defined modules
from Loki.TheFlashModule import FileNames, FlashData
from Loki.TheUsefulModule import WWFnF, WWLists, WWTerminal


## ###############################################################
## PROGRAM PARAMTERS
## ###############################################################
BOOL_RUN_JOBS = 0

BOOL_ALFVENIC_SIMS = 0
LIST_SONIC_MACH    = [ 0.5, 2, 4, 6, 8, 10 ]
LIST_ALFVENIC_MACH = [ 0.1, 0.5, 1, 2, 4, 6, 8, 10 ]

BOOL_SSD_SIMS      = 1
LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/" ]
LIST_SUITE_FOLDERS = [ "Rm3000" ]
LIST_MACH_FOLDERS  = [ "Mach0.2" ]
LIST_SIM_FOLDERS   = [ "Pm5" ]
LIST_RES_FOLDERS   = [ "144" ]


# LIST_SUITE_FOLDERS = [ "Re500", "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
# LIST_RES_FOLDERS   = [ "288" ]


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def convertFloatToStr(float_num):
  if np.log10(float_num) < 0: float_format = "{:.1g}"
  else: float_format = "{:.0f}"
  return float_format.format(float_num).replace(".", "")

def createFileName(filename, sim_regime):
  job_name_pre  = filename.split(".")[0]
  job_name_post = filename.split(".")[1]
  return f"{job_name_pre}_{sim_regime}.{job_name_post}" 


## ###############################################################
## OPPERATOR CLASS
## ###############################################################
class JobProcessCurvature():
  def __init__(
      self,
      sim_name, sim_regime, directory_inputs, directory_outputs, num_cells, num_blocks, max_mem,
      index_start  = None,
      index_end    = None,
      num_files    = None,
      bool_verbose = True,
    ):
    if not WWFnF.checkDirectoryExists(directory_inputs):  raise Exception(f"Error: directory does not exist: {directory_inputs}")
    if not WWFnF.checkDirectoryExists(directory_outputs): raise Exception(f"Error: directory does not exist: {directory_outputs}")
    self.directory_outputs = directory_outputs
    num_blocks_str = " ".join(
      str(val)
      for val in num_blocks
    )
    self.bool_verbose = bool_verbose
    self.max_hours    = int(24)
    self.max_mem      = int(max_mem)
    self.num_procs    = int(self.max_mem // 4)
    ## check group project
    if   "ek9" in self.directory_outputs: self.group_project = "ek9"
    elif "jh2" in self.directory_outputs: self.group_project = "jh2"
    else: raise Exception("Error: undefined group project.")
    self.job_name     = createFileName(FileNames.FILENAME_PROCESS_CURVATURE_JOB, sim_regime)
    self.job_output   = createFileName(FileNames.FILENAME_PROCESS_CURVATURE_OUTPUT, sim_regime)
    self.job_tagname  = f"{sim_name}_kappa"
    ## define executed command
    self.command = FileNames.FILENAME_PROCESS_CURVATURE_SCRIPT
    self.command += f" -sim_name {sim_name}"
    self.command += f" -sim_regime {sim_regime}"
    self.command += f" -directory_inputs {directory_inputs}"
    self.command += f" -directory_outputs {self.directory_outputs}"
    self.command += f" -num_cells {num_cells}"
    self.command += f" -num_blocks {num_blocks_str}"
    if index_start is not None: self.command += f" -index_start {int(index_start)}"
    if index_end   is not None: self.command += f" -index_end {int(index_end)}"
    if num_files   is not None: self.command += f" -num_files {int(num_files)}"
    # self.command += f" -force_process"
    # self.command += f" -update_summary"

  def createJob(self):
    ## create/overwrite job file
    with open(f"{self.directory_outputs}/{self.job_name}", "w") as job_file:
      ## write contents
      job_file.write("#!/bin/bash\n")
      job_file.write(f"#PBS -P {self.group_project}\n")
      job_file.write("#PBS -q normal\n")
      job_file.write(f"#PBS -l walltime={self.max_hours}:00:00\n")
      job_file.write(f"#PBS -l ncpus={self.num_procs}\n")
      job_file.write(f"#PBS -l mem={self.max_mem}GB\n")
      job_file.write(f"#PBS -l storage=scratch/{self.group_project}+gdata/{self.group_project}\n")
      job_file.write("#PBS -l wd\n")
      job_file.write(f"#PBS -N {self.job_tagname}\n")
      job_file.write("#PBS -j oe\n")
      job_file.write("#PBS -m bea\n")
      job_file.write(f"#PBS -M neco.kriel@anu.edu.au\n")
      job_file.write("\n")
      job_file.write(f"{self.command} 1>{self.job_output} 2>&1\n")
    ## indicate progress
    if self.bool_verbose:
      print(f"defined PBS job:")
      print(f"\t> Job name:",  self.job_name)
      print(f"\t> Directory:", self.directory_outputs)


## ###############################################################
## MAIN PROGRAMS
## ###############################################################
def main_alfvenic():
  path_sims    = "/scratch/jh2/jb2980/turbulent_boxes"
  path_outputs = "/scratch/jh2/nk7952/alfvenic_sims"
  print("Checking alfvenic simulations:", path_sims, "\n")
  for sonic_mach in LIST_SONIC_MACH:
    for alfvenic_mach in LIST_ALFVENIC_MACH:
      sonic_mach_str    = convertFloatToStr(sonic_mach)
      alfvenic_mach_str = convertFloatToStr(alfvenic_mach)
      sim_name          = f"M{sonic_mach_str}MA{alfvenic_mach_str}"
      directory_inputs   = f"{path_sims}/{sim_name}"
      if not(os.path.exists(directory_inputs)): continue
      print("Looking at:", directory_inputs)
      directory_outputs = f"{path_outputs}/{sim_name}"
      WWFnF.createDirectory(directory_outputs)
      JobProcessCurvature(
        sim_name         = sim_name,
        directory_inputs  = directory_inputs,
        directory_outputs = directory_outputs,
        num_cells        = 576,
        num_blocks       = [ 24, 36, 36 ],
        max_mem          = 48 # GB (should always be a multiple of 4)
      ).createJob()
      if BOOL_RUN_JOBS: WWTerminal.submitJob(directory_outputs, FileNames.FILENAME_PROCESS_CURVATURE_JOB)
      print(" ")

def main_ssd():
  list_directory_sims = FlashData.getListOfSimDirectories(
    list_base_paths    = LIST_BASE_PATHS,
    list_suite_folders = LIST_SUITE_FOLDERS,
    list_mach_folders  = LIST_MACH_FOLDERS,
    list_sim_folders   = LIST_SIM_FOLDERS,
    list_res_folders   = LIST_RES_FOLDERS
  )
  print("Checking SSD simulations\n")
  for directory_sim in list_directory_sims:
    print("Looking at:", directory_sim)
    directory_plt = f"{directory_sim}/plt/"
    dict_sim_inputs = FlashData.readSimInputs(directory_sim, bool_verbose=False)
    num_cells = dict_sim_inputs["num_blocks"][0] * dict_sim_inputs["num_procs"][0]
    outputs_per_t_turb = dict_sim_inputs["outputs_per_t_turb"]
    list_plt_filenames = WWFnF.getFilesInDirectory(
      directory             = directory_plt,
      filename_starts_with  = FileNames.FILENAME_FLASH_PLT_FILES,
      filename_not_contains = "spect",
      loc_file_index        = 4
    )
    list_file_indices = [
      int(plt_filename.split("_")[-1])
      for plt_filename in list_plt_filenames
    ]
    list_t_turb = [
      float(file_index / outputs_per_t_turb)
      for file_index in list_file_indices
    ]
    dict_sim_summary = FlashData.readSimSummary(directory_sim)
    time_nl_start = dict_sim_summary["nl_regime"]["start_time"]
    time_nl_end   = dict_sim_summary["nl_regime"]["end_time"]
    index_nl_start = WWLists.getIndexClosestValue(list_t_turb, time_nl_start)
    index_nl_end   = WWLists.getIndexClosestValue(list_t_turb, time_nl_end)
    for ssd_regime in [
        "exp_regime",
        "nl_regime",
        "sat_regime",
      ]:
      index_start = None
      index_end   = None
      if ("exp" in ssd_regime): index_end   = list_file_indices[index_nl_start]
      if ("sat" in ssd_regime): index_start = list_file_indices[index_nl_end]
      if ("nl"  in ssd_regime):
        index_start = list_file_indices[index_nl_start]
        index_end   = list_file_indices[index_nl_end]
      if (index_start is None) and (index_end is None): raise Exception("Error: START and END indiced should be defined.")
      JobProcessCurvature(
        sim_name          = FlashData.getJobTag(dict_sim_inputs, ssd_regime.split("_")[0]),
        sim_regime       = ssd_regime,
        directory_inputs  = directory_plt,
        directory_outputs = directory_sim,
        index_start       = index_start,
        index_end         = index_end,
        num_cells         = num_cells,
        num_blocks        = dict_sim_inputs["num_blocks"],
        max_mem           = 48, # GB (should always be a multiple of 4)
      ).createJob()
      job_name = createFileName(FileNames.FILENAME_PROCESS_CURVATURE_JOB, ssd_regime)
      if BOOL_RUN_JOBS: WWTerminal.submitJob(directory_sim, job_name)
    print(" ")

def main():
  if BOOL_ALFVENIC_SIMS: main_alfvenic()
  if BOOL_SSD_SIMS:      main_ssd()


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM