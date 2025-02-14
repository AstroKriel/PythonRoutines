#!/usr/bin/env python3

## ###############################################################
## MODULES
## ###############################################################
import h5py
import numpy as np

## load new user defined modules
from TheUsefulModule import WWArgparse, WWFnF, WWTerminal


## ###############################################################
## DEFINE DATASET PROPERTIES
## ###############################################################
DICT_PLT_ARGS = {
  "current": {
    "name": "Current Density Field",
    "dataset": [ "curx", "cury", "curz" ]
  },
  "tension": {
    "name": "Magnetic Tension Field",
    "dataset": [ "tenx", "teny", "tenz" ]
  }
}

DICT_SPECT_ARGS = {
  "kin" : {
    "name": "Kinetic Energy Spectrum",
    "input_args": {
      "flag": 7,
      "dataset": [ "rho", "velx", "vely", "velz" ]
    },
    "output_name": "sqrtrho",
    "rename": "kinetic"
  },
  "vel" : {
    "name": "Velocity Magnitude Spectrum",
    "input_args": {
      "flag": 0,
      "dataset": [ "velx", "vely", "velz" ]
    },
    "output_name": "dset_velx_vely_velz",
    "rename": "velocity"
  },
  "mag" : {
    "name": "Magnetic Energy Spectrum",
    "input_args": {
      "flag": 0,
      "dataset": [ "magx", "magy", "magz" ]
    },
    "output_name": "dset_magx_magy_magz",
    "rename": "magnetic"
  },
  "cur" : {
    "name": "Current Density Spectrum",
    "input_args": {
      "flag": 0,
      "dataset": [ "curx", "cury", "curz" ]
    },
    "output_name": "dset_curx_cury_curz",
    "rename": "current"
  },
  "ten" : {
    "name": "Magnetic Tension Spectrum",
    "input_args": {
      "flag": 0,
      "dataset": [ "tenx", "teny", "tenz" ]
    },
    "output_name": "dset_tenx_teny_tenz",
    "rename": "tension"
  }
}


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def checkAllSpectDatasetsAreValid(list_spect_datasets):
  invalid_datasets = []
  for spect_dataset in list_spect_datasets:
    if spect_dataset not in DICT_SPECT_ARGS: invalid_datasets.append(f"'{spect_dataset}'")
  if len(invalid_datasets) > 0: raise KeyError(f"The following dataset are not valid: {', '.join(invalid_datasets)}")

def getAllRequiredPltCommands(list_spect_datasets):
  set_plt_commands = {
    plt_command
    for spect_dataset in list_spect_datasets
    for plt_data in DICT_SPECT_ARGS[spect_dataset]["input_args"]["dataset"]
    for plt_command in DICT_PLT_ARGS.keys()
    if plt_data in DICT_PLT_ARGS[plt_command]["dataset"]
  }
  return sorted(list(set_plt_commands))

def checkWhichPltDataToDerive(filename, list_plt_commands_to_check):
  set_missing_dataset = set()
  set_commands_to_run = set()
  with h5py.File(filename, "r") as fp:
    list_stored_datasets = list(fp.keys())
    for plt_command in list_plt_commands_to_check:
      for plt_dataset in DICT_PLT_ARGS[plt_command]["dataset"]:
        if plt_dataset not in list_stored_datasets:
          set_missing_dataset.add(plt_dataset)
          set_commands_to_run.add(plt_command)
  return list(set_missing_dataset), list(set_commands_to_run)


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class ProcessPltFiles():
  def __init__(self):
    args_list = { "nargs":"*", "default":[] }
    parser = WWArgparse.MyParser(description="Calculate kinetic and magnetic energy spectra.")
    ## ------------------- DEFINE OPTIONAL ARGUMENTS
    args_opt = parser.add_argument_group(description="Optional processing arguments:")
    args_opt.add_argument("-debug",            **WWArgparse.OPT_BOOL_ARG, default=False)
    args_opt.add_argument("-process_all",      **WWArgparse.OPT_BOOL_ARG, default=True)
    args_opt.add_argument("-spect_datasets",   **WWArgparse.OPT_ARG, type=str, **args_list)
    args_opt.add_argument("-file_start_index", **WWArgparse.OPT_ARG, type=int, default=0)
    args_opt.add_argument("-file_end_index",   **WWArgparse.OPT_ARG, type=int, default=np.inf)
    args_opt.add_argument("-num_procs",        **WWArgparse.OPT_ARG, type=int, default=8)
    ## ------------------- DEFINE REQUIRED ARGUMENTS
    args_req = parser.add_argument_group(description="Required processing arguments:")
    args_req.add_argument("-data_path", type=str, required=True, help="type: %(type)s")
    ## open arguments
    args = vars(parser.parse_args())
    ## save parameters
    self.bool_debug          = args["debug"]
    self.bool_process_all    = args["process_all"]
    self.list_spect_datasets = args["spect_datasets"]
    self.file_start_index    = args["file_start_index"]
    self.file_end_index      = args["file_end_index"]
    self.num_procs           = args["num_procs"]
    self.filepath_data       = args["data_path"]
    ## interpret optional arguments
    str_condition = "All" if self.bool_process_all else "All unprocessed"
    checkAllSpectDatasetsAreValid(self.list_spect_datasets)
    self.list_plt_commands = getAllRequiredPltCommands(self.list_spect_datasets)
    ## report input parameters
    WWTerminal.printLine("Processing with the following parameters:")
    if self.bool_debug: WWTerminal.printLine(f"\t> Running in debug mode")
    WWTerminal.printLine(f"\t> Directory: {self.filepath_data}")
    WWTerminal.printLine(f"\t> {str_condition} plt-files in the range: [{self.file_start_index}, {self.file_end_index}]")
    WWTerminal.printLine(f"\t> With {str(self.num_procs)} processors")
    WWTerminal.printLine("")
    if len(self.list_plt_commands) > 0:
      WWTerminal.printLine("Will derive the following plt-dataset (if they do not already exist).")
      WWTerminal.printLine([
        f"\t> {DICT_PLT_ARGS[plt_command]['dataset']} ({DICT_PLT_ARGS[plt_command]['name']})\n"
        for plt_command in self.list_plt_commands
      ])
    else: WWTerminal.printLine("No plt-dataset need to be derived.\n")
    if len(self.list_spect_datasets) > 0:
      WWTerminal.printLine("Will compute the following spect-dataset (where necessary).")
      WWTerminal.printLine([
        f"\t> {spect_dataset} ({DICT_SPECT_ARGS[spect_dataset]['name']})\n"
        for spect_dataset in self.list_spect_datasets
      ])
    else: WWTerminal.printLine("No spect-dataset have been requested\n")

  def performRoutine(self):
    if len(self.list_spect_datasets) == 0:
      WWTerminal.printLine("There's no work to do. Exiting program.")
      return
    list_plt_files = WWFnF.getFilesInDirectory(
      directory             = self.filepath_data,
      filename_contains     = "plt",
      filename_not_contains = "spect",
      loc_file_index        = 4,
      file_start_index      = self.file_start_index,
      file_end_index        = self.file_end_index
    )
    if self.bool_process_all:
      if len(list_plt_files) > 0: self._processPltFiles(list_plt_files)
      else: WWTerminal.printLine("There are no plt-files to process.\n")
    list_plt_files_to_reprocess = self._checkWhichPltFilesToReProcess(list_plt_files)
    if len(list_plt_files_to_reprocess) > 0: self._processPltFiles(list_plt_files_to_reprocess[:5])
    else: WWTerminal.printLine("There are no plt-files to re-process.\n")
    WWTerminal.printLine("Finished processing files.")

  def _checkWhichPltFilesToReProcess(self, list_plt_filenames):
    WWTerminal.printLine("Checking which plt-files need to be reprocessed...")
    dict_spect_files = {}
    for spect_dataset in self.list_spect_datasets:
      _list_spect_filenames = WWFnF.getFilesInDirectory(
        directory          = self.filepath_data,
        filename_contains  = "plt",
        filename_ends_with = f"spect_{DICT_SPECT_ARGS[spect_dataset]['rename']}.dat",
        loc_file_index     = 4,
        file_start_index   = self.file_start_index,
        file_end_index     = self.file_end_index
      )
      dict_spect_files[spect_dataset] = _list_spect_filenames
    list_plt_filenames_to_process = []
    for plt_filename in list_plt_filenames:
      for spect_dataset in self.list_spect_datasets:
        spect_filename = f"{plt_filename}_spect_{DICT_SPECT_ARGS[spect_dataset]['rename']}.dat"
        if spect_filename not in dict_spect_files[spect_dataset]:
          list_plt_filenames_to_process.append(plt_filename)
          break
    return list_plt_filenames_to_process

  def _processPltFiles(self, list_filenames):
    WWTerminal.printLine(f"There are {len(list_filenames)} plt-files to (re)process:")
    WWTerminal.printLine("\t> " + "\n\t> ".join(list_filenames) + "\n")
    for filename in list_filenames:
      WWTerminal.printLine(f"------------------------------------------")
      WWTerminal.printLine(f"-> Looking at: {filename}")
      WWTerminal.printLine(f"------------------------------------------\n")
      self.__derivePltFileData(filename)
      self.__computeSpectra(filename)

  def _runCommand(self, command):
    if self.bool_debug: print(command)
    else: WWTerminal.runCommand(command, self.filepath_data)

  def _runMPICommand(self, command_args):
    self._runCommand(f"mpirun -np {self.num_procs} {command_args}")

  def __derivePltFileData(self, filename):
    list_missing_plt_dataset, list_plt_commands_to_run = checkWhichPltDataToDerive(filename, self.list_plt_commands)
    if len(list_missing_plt_dataset) > 0:
      WWTerminal.printLine("The following plt-dataset need to be derived:")
      WWTerminal.printLine("\t> " + "\n\t> ".join(list_missing_plt_dataset) + "\n")
      for plt_command in list_plt_commands_to_run:
        plt_dataset_name = DICT_PLT_ARGS[plt_command]["name"]
        WWTerminal.printLine(f"> Deriving {plt_dataset_name}...\n")
        self._runMPICommand(f"derivative_var {filename} -{plt_command}")
    else: WWTerminal.printLine("All necessary plt-dataset are already present.\n")

  def __computeSpectra(self, filename):
    for spect_dataset in self.list_spect_datasets:
      filename_spect_new = f"{filename}_spect_{DICT_SPECT_ARGS[spect_dataset]['rename']}.dat"
      spect_dataset_name = DICT_SPECT_ARGS[spect_dataset]["name"]
      if not(WWFnF.checkFileExists(self.filepath_data, filename_spect_new)):
        WWTerminal.printLine(f"> Processing {spect_dataset_name}...\n")
        spect_flag = DICT_SPECT_ARGS[spect_dataset]["input_args"]["flag"]
        spect_command = f"-types {spect_flag}"
        if spect_flag == 0: spect_command += " -dsets " + " ".join(DICT_SPECT_ARGS[spect_dataset]["input_args"]["dataset"])
        self._runMPICommand(f"spectra_mpi {filename} {spect_command}")
      else: WWTerminal.printLine(f"{spect_dataset_name} has already been processed.\n")
      filename_spect_old = f"{filename}_spect_{DICT_SPECT_ARGS[spect_dataset]['output_name']}.dat"
      if WWFnF.checkFileExists(self.filepath_data, filename_spect_old):
        self._runCommand(f"mv {filename_spect_old} {filename_spect_new}")
        WWTerminal.printLine(f"Renamed '{filename_spect_old}' to '{filename_spect_new}'\n")


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  obj_calc_spectra = ProcessPltFiles()
  obj_calc_spectra.performRoutine()


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()


## END OF PROGRAM