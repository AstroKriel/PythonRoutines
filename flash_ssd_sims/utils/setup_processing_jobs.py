## ###############################################################
## MODULES
## ###############################################################
import sys

## load user defined modules
from Loki.TheFlashModule import FlashData, FileNames
from Loki.TheUsefulModule import WWFnF, WWTerminal


## ###############################################################
## PROGRAM PARAMETERS
## ###############################################################
BOOL_DEFINE_JOB = 1
BOOL_RUN_JOB    = 1
BOOL_MPROC      = 1
BOOL_DEBUG_MODE = 0

# JOB_NAME        = "job_collect_spectra.sh"
# JOB_COMMAND     = lambda directory: f"collect_sim_spectra.py -sim_path {directory}"
# DICT_JOB_PARAMS = {
#   "max_hours"     : 2,
#   "num_procs"     : 8,
#   "job_tagname"   : "collect",
# }

# JOB_NAME        = "job_compute_srt_spectra.sh"
# JOB_COMMAND     = lambda directory: f"compute_srt_spectra.py -sim_path {directory} -save_data"
# DICT_JOB_PARAMS = {
#   "max_hours"     : 24,
#   "num_procs"     : 8*3,
#   "job_tagname"   : "srt",
# }

# JOB_NAME        = "job_compute_cross_helicity_spectra.sh"
# JOB_COMMAND     = lambda directory: f"compute_cross_helicity_spectra.py -sim_path {directory} -save_data"
# DICT_JOB_PARAMS = {
#   "max_hours"     : 24,
#   "num_procs"     : 8*3,
#   "job_tagname"   : "ch",
# }

# JOB_NAME        = "job_measure_SSD_phases.sh"
# JOB_COMMAND     = lambda directory: f"measure_SSD_phases.py -sim_path {directory} -save_data"
# DICT_JOB_PARAMS = {
#   "max_hours"     : 2,
#   "num_procs"     : 8,
#   "job_tagname"   : "phases",
# }

JOB_NAME        = "job_plot_sim_data.sh"
JOB_COMMAND     = lambda directory: f"plot_sim_data.py -sim_path {directory} -save_data"
DICT_JOB_PARAMS = {
  "max_hours"     : 2,
  "num_procs"     : 8,
  "job_tagname"   : "plot",
}

# ## full list of ek9 simulations
# LIST_BASE_PATHS    = [ "/scratch/ek9/nk7952/" ]
# LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
# LIST_RES_FOLDERS   = [ "576" ]
# LIST_SIM_NAMES     = [ ]
# SUBFOLDER          = ""

# ## full list of jh2 simulations
# LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/" ]
# LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
# LIST_RES_FOLDERS   = [ "18", "36", "72", "144", "288", "576", "1152" ]
# LIST_SIM_NAMES     = [ ]
# SUBFOLDER          = ""


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def createJobScript(directory):
  if   "/jh2/" in directory: group_project = "jh2"
  elif "/ek9/" in directory: group_project = "ek9"
  else: raise Exception("Error: could not identify project from the directory")
  max_hours     = DICT_JOB_PARAMS["max_hours"]
  num_procs     = DICT_JOB_PARAMS["num_procs"]
  max_mem       = num_procs * 4
  sim_name      = FlashData.getSimName(FlashData.readSimInputs(directory, bool_verbose=False))
  job_tagname   = sim_name + DICT_JOB_PARAMS["job_tagname"]
  job_output    = JOB_NAME.replace(".sh", ".out").replace("job_", "shell_")
  with open(f"{directory}/{JOB_NAME}", "w") as job_file:
    ## write contents
    job_file.write("#!/bin/bash\n")
    job_file.write(f"#PBS -P {group_project}\n")
    job_file.write("#PBS -q normal\n")
    job_file.write(f"#PBS -l walltime={max_hours}:00:00\n")
    job_file.write(f"#PBS -l ncpus={num_procs}\n")
    job_file.write(f"#PBS -l mem={max_mem}GB\n")
    job_file.write(f"#PBS -l storage=scratch/{group_project}+gdata/{group_project}\n")
    job_file.write("#PBS -l wd\n")
    job_file.write(f"#PBS -N {job_tagname}\n")
    job_file.write("#PBS -j oe\n")
    job_file.write("#PBS -m bea\n")
    job_file.write(f"#PBS -M neco.kriel@anu.edu.au\n")
    job_file.write("\n")
    job_file.write(". ~/modules_flash\n")
    job_file.write(f"{JOB_COMMAND(directory)} 1>{job_output} 2>&1\n")
  ## indicate progress
  print(f"Successfully defined PBS job: {directory}/{JOB_NAME}")

def evalJobInDirectory(
    directory_sim,
    job_index = None,
    num_jobs  = None,
    **kwargs
  ):
  dict_sim_inputs = FlashData.readSimInputs(directory_sim, bool_verbose=False)
  sim_name = FlashData.getSimName(dict_sim_inputs)
  if len(LIST_SIM_NAMES) > 0:
    if not(sim_name in LIST_SIM_NAMES): return
  if (job_index is not None) and (num_jobs is not None): print(f"({job_index+1}/{num_jobs})")
  directory_job = WWFnF.createFilepath([directory_sim, SUBFOLDER])
  bool_sim_job_running  = WWFnF.checkIfJobIsRunning(directory_sim, FileNames.FILENAME_RUN_SIM_JOB)
  bool_plt_job_running  = WWFnF.checkIfJobIsRunning(f"{directory_sim}/plt/", FileNames.FILENAME_PROCESS_PLT_JOB)
  bool_this_job_running = WWFnF.checkIfJobIsRunning(directory_sim, JOB_NAME)
  if any([bool_sim_job_running, bool_plt_job_running, bool_this_job_running]):
    print(f"Job `{JOB_NAME}` is busy running in: {directory_job}\n")
    return
  if BOOL_DEFINE_JOB: createJobScript(directory_job)
  if BOOL_DEBUG_MODE:
    print(f"Running in debug mode: {directory_job}\n")
    return
  if BOOL_RUN_JOB: WWTerminal.submitJob(directory_job, JOB_NAME)
  if not BOOL_MPROC: print(" ")


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
  num_jobs = len(list_directory_sims)
  if BOOL_MPROC:
    FlashData.callFuncForAllDirectories(evalJobInDirectory, list_directory_sims)
  else:
    [
      evalJobInDirectory(directory_sim, sim_index, num_jobs)
      for sim_index, directory_sim in enumerate(list_directory_sims)
    ]


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM