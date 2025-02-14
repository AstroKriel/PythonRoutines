## ###############################################################
## MODULES
## ###############################################################
import sys, shutil
import numpy as np

## load user defined modules
from TheFlashModule import FileNames, FlashData, JobRunSim, LoadData
from TheUsefulModule import WWTerminal, WWFnF, WWArgparse, WWObjs


## ###############################################################
## PROGRAM PARAMTERS
## ###############################################################
BOOL_IGNORE_JOB = 0
BOOL_DEBUG_MODE = 0

# LIST_BASE_PATHS    = [ "/scratch/ek9/nk7952/" ]
# LIST_SUITE_FOLDERS = [  ]
# LIST_MACH_FOLDERS  = [  ]
# LIST_SIM_FOLDERS   = [  ]
# LIST_RES_FOLDERS   = [  ]
# LIST_SIM_NAMES     = [  ]


## ###############################################################
## OPPERATOR CLASS
## ###############################################################
class RestartSim:
  def __init__(
      self,
      directory_sim,
      new_Tmax  = None,
      new_cfl   = None,
      max_hours = None
    ):
    self.directory_sim = directory_sim
    self.new_Tmax      = new_Tmax
    self.new_cfl       = new_cfl
    self.max_hours     = max_hours
    self.performRoutine()

  def __backupFile(self, filename_old):
    filename_new = f"{filename_old}_backup{self.prev_run_index_str}"
    shutil.move(
      f"{self.directory_sim}/{filename_old}",
      f"{self.directory_sim}/{filename_new}"
    )
    print(f"\t> Backed up '{filename_old}' as '{filename_new}'")

  def performRoutine(self):
    print("Looking at:", self.directory_sim)
    if not(BOOL_IGNORE_JOB) and WWFnF.checkIfJobIsRunning(self.directory_sim, FileNames.FILENAME_RUN_SIM_JOB):
      print("\t> Simulation is currently running")
      return
    if BOOL_DEBUG_MODE: return
    self.dict_sim_inputs = FlashData.readSimInputs(self.directory_sim)
    self.prev_run_index = self.dict_sim_inputs["run_index"]
    self.prev_run_index_str = str(self.prev_run_index).zfill(2)
    ## extend the simulation duration if needed
    if self.new_Tmax is not None: self.dict_sim_inputs["max_num_t_turb"] = self.new_Tmax
    if self.new_cfl  is not None: self.dict_sim_inputs["cfl"]            = self.new_cfl
    ## check that the simulation has run for the desired duration
    sim_duration = np.max(LoadData.loadVIData(
      directory  = self.directory_sim,
      field_name = "mach",
      t_turb     = self.dict_sim_inputs["t_turb"]
    )[0])
    ## only restart if the simulation needs to run for longer
    if np.abs(self.dict_sim_inputs["max_num_t_turb"] - sim_duration) > 2: self._prepForRestart()
    else: print("\t> No need to restart the simulation. The simulation has run for the desired duration.")

  def _prepForRestart(self):
    ## if the previous setup has run
    if WWFnF.checkFileExists(self.directory_sim, f"{FileNames.FILENAME_RUN_SIM_OUTPUT}{self.prev_run_index_str}"):
      ## create a backup of the simulation input files
      self.__backupFile(FileNames.FILENAME_SIM_INPUTS)
      self.__backupFile(FileNames.FILENAME_FLASH_INPUT)
      ## create a new simulation input file
      self.dict_sim_inputs["run_index"] = self.prev_run_index + 1
    else: print("\t> No need to backup files. The current run has not been executed yet.")
    ## save the updated simulation input file
    WWObjs.saveDict2JsonFile(f"{self.directory_sim}/{FileNames.FILENAME_SIM_INPUTS}", self.dict_sim_inputs)
    ## create a new flash input file
    obj_prep_sim = JobRunSim.JobRunSim(
      directory_sim   = self.directory_sim,
      dict_sim_inputs = self.dict_sim_inputs,
      max_hours       = self.max_hours
    )
    obj_prep_sim.prepForRestart()
    ## submit simulation if it needs to run for longer
    WWTerminal.submitJob(
      directory       = self.directory_sim,
      job_name        = FileNames.FILENAME_RUN_SIM_JOB,
      bool_ignore_job = BOOL_IGNORE_JOB,
    )


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  ## ------------------- RECEIVE USER INPUT
  parser = WWArgparse.MyParser(description="Restart simulation.")
  ## optional arguments
  args_opt = parser.add_argument_group(description="Optional processing arguments:")
  args_opt.add_argument("-new_Tmax",   **WWArgparse.OPT_ARG, default=None)
  args_opt.add_argument("-new_cfl",    **WWArgparse.OPT_ARG, default=None)
  args_opt.add_argument("-max_hours",  **WWArgparse.OPT_ARG, default=None)
  args_opt.add_argument("-sim_path", type=str, required=False, help="type: %(type)s")
  ## open arguments
  args = vars(parser.parse_args())
  ## save parameters
  directory_sim = args["sim_path"]
  new_Tmax  = None if args["new_Tmax"]  is None else int(args["new_Tmax"])
  new_cfl   = None if args["new_cfl"]   is None else float(args["new_cfl"])
  max_hours = None if args["max_hours"] is None else int(args["max_hours"])
  ## run 
  if directory_sim is None:
    FlashData.callFuncForAllSimulations(
      func               = RestartSim,
      list_base_paths    = LIST_BASE_PATHS,
      list_suite_folders = LIST_SUITE_FOLDERS,
      list_mach_folders  = LIST_MACH_FOLDERS,
      list_sim_folders   = LIST_SIM_FOLDERS,
      list_res_folders   = LIST_RES_FOLDERS,
    )
  else:
    RestartSim(
      directory_sim = directory_sim,
      new_Tmax      = new_Tmax,
      new_cfl       = new_cfl,
      max_hours     = max_hours,
    )
    print(" ")


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM