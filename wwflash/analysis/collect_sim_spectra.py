#!/bin/env python3


## ###############################################################
## MODULES
## ###############################################################
import sys, functools
import xarray as xr

## load user defined modules
from TheFlashModule import LoadData, FlashData, FileNames
from TheUsefulModule import WWFnF, WWArgparse, WWTerminal


## ###############################################################
## PROGRAM PARAMETERS
## ###############################################################
LIST_BASE_PATHS = [ "/scratch/jh2/nk7952/" ]

# ## full list of simulations
# BOOL_MPROC         = 1
# LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
# LIST_RES_FOLDERS   = [ "18", "36", "72", "144", "288", "576", "1152" ]


## ###############################################################
## OPPERATOR HANDLING PLOT CALLS
## ###############################################################
def collectSimSpectra(
    directory_sim,
    bool_verbose = True,
    **kwargs
  ):
  WWTerminal.printLine(f"Looking at: {directory_sim}")
  directory_spect = f"{directory_sim}/spect/"
  dict_sim_inputs = FlashData.readSimInputs(directory_sim)
  outputs_per_t_turb = dict_sim_inputs["outputs_per_t_turb"]
  print("Reading kinetic energy spectra...")
  dict_kin_spectrum = LoadData.loadAllSpectra(
    directory          = directory_spect,
    spect_field        = "kin",
    spect_comp         = "tot",
    outputs_per_t_turb = outputs_per_t_turb,
    bool_verbose       = bool_verbose
  )
  print("Reading magnetic energy spectra...")
  dict_mag_spectrum = LoadData.loadAllSpectra(
    directory          = directory_spect,
    spect_field        = "mag",
    spect_comp         = "tot",
    outputs_per_t_turb = outputs_per_t_turb,
    bool_verbose       = bool_verbose
  )
  print("Reading current density power spectra...")
  dict_cur_spectrum = LoadData.loadAllSpectra(
    directory          = directory_spect,
    spect_field        = "cur",
    spect_comp         = "tot",
    outputs_per_t_turb = outputs_per_t_turb,
    bool_verbose       = bool_verbose
  )
  if not WWFnF.checkFileExists(directory_sim, FileNames.FILENAME_SIM_OUTPUTS):
    print("Creating a fresh dataset.")
    ds = xr.Dataset()
  else: ds = FlashData.readSimOutputs(directory_sim)
  ds = FlashData.addSpectrum2Xarray(
    ds            = ds,
    dict_spectrum = dict_kin_spectrum,
    spectrum_name = "kinetic_energy_spectra",
  )
  ds = FlashData.addSpectrum2Xarray(
    ds            = ds,
    dict_spectrum = dict_mag_spectrum,
    spectrum_name = "magnetic_energy_spectra",
  )
  ds = FlashData.addSpectrum2Xarray(
    ds            = ds,
    dict_spectrum = dict_cur_spectrum,
    spectrum_name = "current_density_spectra",
  )
  ds = FlashData.saveSimOutputs(ds, directory_sim)
  if bool_verbose: WWTerminal.printLine(" ")


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  parser = WWArgparse.MyParser(description="Plot and derive all relevant SSD data.")
  args_opt = parser.add_argument_group(description="Optional processing arguments:")
  args_opt.add_argument("-sim_path", type=str, required=False, default=None, help="type: %(type)s")
  args = vars(parser.parse_args())
  directory_sim = args["sim_path"]
  if directory_sim is None:
    FlashData.callFuncForAllSimulations(
      func               = functools.partial(collectSimSpectra, bool_verbose=False),
      bool_mproc         = BOOL_MPROC,
      list_base_paths    = LIST_BASE_PATHS,
      list_suite_folders = LIST_SUITE_FOLDERS,
      list_mach_folders  = LIST_MACH_FOLDERS,
      list_sim_folders   = LIST_SIM_FOLDERS,
      list_res_folders   = LIST_RES_FOLDERS,
    )
  else:
    if WWFnF.checkDirectoryExists(directory_sim): collectSimSpectra(directory_sim)
    else: raise Exception("Directory does not exist.")


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM