## ###############################################################
## MODULES
## ###############################################################
import sys

## load user defined modules
from Loki.TheFlashModule import FileNames, FlashData, LoadData, JobRunSim
from Loki.TheUsefulModule import WWFnF, WWTerminal


## ###############################################################
## PROGRAM PARAMETERS
## ###############################################################
BOOL_CREATE_SIM_INPUTS  = 0
BOOL_CREATE_SIM_JOB     = 0
REFERENCE_RES_FOLDER    = None
BOOL_IGNORE_SIM_STATUS  = 1
BOOL_SUBMIT_SIM_JOB     = 1

LIST_BASE_PATHS = [ "/scratch/jh2/nk7952/" ]

LIST_SUITE_FOLDERS = [ "Re500" ]
LIST_MACH_FOLDERS  = [ "Mach0.5", "Mach1", "Mach2", "Mach10" ]
LIST_SIM_FOLDERS   = [ "Pm1" ]
# LIST_RES_FOLDERS   = [ "288" ]
LIST_RES_FOLDERS   = [
  f"288v{v_index}"
  for v_index in range(2, 11)
]


## ###############################################################
## CREATE JOB SCRIPT
## ###############################################################
def createJobs(directory_sim, dict_sim_inputs):
  obj_prep_sim = JobRunSim.JobRunSim(directory_sim, dict_sim_inputs)
  if not(REFERENCE_RES_FOLDER is None) and not(REFERENCE_RES_FOLDER == ""):
    filepath_ref = directory_sim.replace(dict_sim_inputs["res_folder"], REFERENCE_RES_FOLDER)
    print("here", filepath_ref)
    if not WWFnF.checkDirectoryExists(filepath_ref): raise Exception("Error: the provided reference simulation-folder does not exist:", filepath_ref)
    obj_prep_sim.prepFromReference(filepath_ref)
  else: obj_prep_sim.prepFromTemplate()


## ###############################################################
## LOOP OVER AND GET ALL SIMULATION DETAILS
## ###############################################################
def getSimInputDetails():
  return [
    {
      "directory_sim" : WWFnF.createFilepath([ base_path, suite_folder, mach_folder, sim_folder, res_folder ]),
      "suite_folder" : suite_folder,
      "sim_folder"   : sim_folder,
      "res_folder"   : res_folder,
      "desired_Mach" : LoadData.getNumberFromString(mach_folder,  "Mach"),
      "Re"           : LoadData.getNumberFromString(suite_folder, "Re"),
      "Rm"           : LoadData.getNumberFromString(suite_folder, "Rm"),
      "Pm"           : LoadData.getNumberFromString(sim_folder,   "Pm")
    }
    for base_path    in LIST_BASE_PATHS
    for suite_folder in LIST_SUITE_FOLDERS
    for mach_folder  in LIST_MACH_FOLDERS
    for sim_folder   in LIST_SIM_FOLDERS
    for res_folder   in LIST_RES_FOLDERS
    if WWFnF.checkDirectoryExists(
      WWFnF.createFilepath([ base_path, suite_folder, mach_folder, sim_folder, res_folder ])
    )
  ]


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  index_job = 1
  list_sim_dicts = getSimInputDetails()
  num_jobs = len(list_sim_dicts)
  for dict_sim in list_sim_dicts:
    directory_sim = dict_sim["directory_sim"]
    print(f"({index_job}/{num_jobs})")
    print("Looking at:", directory_sim)
    index_job += 1
    bool_sim_inputs_exists = WWFnF.checkFileExists(directory_sim, FileNames.FILENAME_SIM_INPUTS)
    if bool_sim_inputs_exists:
      dict_sim_inputs = FlashData.readSimInputs(directory_sim)
      bool_sim_tuned  = dict_sim_inputs["bool_driving_tuned"]
    else: bool_sim_tuned = False
    if bool_sim_tuned: print("Simulation is already tuned.")
    if not(BOOL_IGNORE_SIM_STATUS) and bool_sim_tuned:
      print(" ")
      continue
    if WWFnF.checkIfJobIsRunning(directory_sim, FileNames.FILENAME_RUN_SIM_JOB):
      print("Job is currently running.")
      print(" ")
      continue
    if BOOL_CREATE_SIM_INPUTS or not(bool_sim_inputs_exists):
      dict_sim_inputs = FlashData.createSimInputs(
        directory     = directory_sim,
        suite_folder  = dict_sim["suite_folder"],
        sim_folder    = dict_sim["sim_folder"],
        res_folder    = dict_sim["res_folder"],
        k_turb        = 2.0,
        desired_Mach  = dict_sim["desired_Mach"],
        Re            = dict_sim["Re"],
        Rm            = dict_sim["Rm"],
        Pm            = dict_sim["Pm"]
      )
    if BOOL_CREATE_SIM_JOB: createJobs(directory_sim, dict_sim_inputs)
    if BOOL_SUBMIT_SIM_JOB and WWFnF.checkFileExists(directory_sim, FileNames.FILENAME_RUN_SIM_JOB):
      WWTerminal.submitJob(directory_sim, FileNames.FILENAME_RUN_SIM_JOB)
    print(" ")
  if index_job == 0: print("There are no simulations in your specified paramater range.")


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM