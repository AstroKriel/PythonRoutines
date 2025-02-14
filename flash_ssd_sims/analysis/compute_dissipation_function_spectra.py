## ###############################################################
## MODULES
## ###############################################################
import os, sys, functools
import numpy as np
import xarray as xr

## 'tmpfile' needs to be loaded before any 'matplotlib' libraries,
## so matplotlib stores its cache in a temporary directory.
## (necessary when plotting in parallel)
import tempfile
os.environ["MPLCONFIGDIR"] = tempfile.mkdtemp()
import matplotlib.pyplot as plt

from aux_funcs import power_spectra_funcs

from TheFlashModule import LoadData, FlashData, FileNames
from TheUsefulModule import WWFnF, WWArgparse, WWTerminal, WWLists
from TheAnalysisModule import WWFields
from ThePlottingModule import PlotFuncs


## ###############################################################
## PREPARE WORKSPACE
## ###############################################################
plt.switch_backend("agg") # use a non-interactive plotting backend


## ###############################################################
## PROGRAM PARAMETERS
## ###############################################################
LIST_BASE_PATHS = [ "/scratch/jh2/nk7952/" ]
BOOL_SAVE_DATA  = 1
BOOL_RECOMPUTE  = 0

## subset of simulations
BOOL_MPROC         = 0
LIST_SUITE_FOLDERS = [ "Rm3000" ]
LIST_MACH_FOLDERS  = [ "Mach0.2" ]
LIST_SIM_FOLDERS   = [ "Pm10" ]
LIST_RES_FOLDERS   = [ "144" ]


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class ComputeVelocityGradientTensorSpectrum():
  def __init__(self, directory_sim, bool_recompute):
    self.spectra_name   = "dissipation_function_spectra"
    self.directory_sim  = directory_sim
    self.bool_recompute = bool_recompute
    self.directory_plt  = f"{self.directory_sim}/plt/"
    self.directory_vis  = f"{self.directory_sim}/vis_folder/"
    WWFnF.createDirectory(self.directory_vis, bool_verbose=False)
    self.dict_sim_inputs = FlashData.readSimInputs(self.directory_sim, bool_verbose=False)
    self.bool_ds_exists  = WWFnF.checkFileExists(self.directory_sim, FileNames.FILENAME_SIM_OUTPUTS)
    if not(self.bool_ds_exists):
      print("Creating a fresh dataset.")
      self.ds = xr.Dataset()
    else:
      self.ds = FlashData.readSimOutputs(self.directory_sim)
      self.bool_spectra_exists = self.spectra_name in self.ds

  def getFittedParams(self):
    return {
      "list_t_turb"     : self.list_t_turb,
      "list_k_turb"     : list(np.arange(1, len(self.spectra_group_t[0])+1)),
      "spectra_group_t" : self.spectra_group_t
    }

  def saveFittedParams(self):
    if len(self.list_t_turb) == 0:
      print("There is no data to save.")
      return
    dict_spectra = self.getFittedParams()
    self.ds = FlashData.addSpectrum2Xarray(self.ds, dict_spectra, self.spectra_name)
    FlashData.saveSimOutputs(self.ds, self.directory_sim)

  def performRoutines(self):
    print(f"Computing {self.spectra_name} in: {self.directory_sim}")
    self.fig, self.ax = plt.subplots(figsize=(7,5))
    self.list_plt_filenames = WWFnF.getFilesInDirectory(
      directory             = self.directory_plt,
      filename_starts_with  = FileNames.FILENAME_FLASH_PLT_FILES,
      filename_not_contains = "spect",
      loc_file_index        = 4
    )
    self._getCmap()
    print(f"There are {len(self.list_plt_filenames)} plt-files...")
    print(" ")
    self.list_t_turb = []
    self.spectra_group_t = []
    if self.bool_ds_exists:
      _list_t_turb = list(self.ds["array_t_turb"].values)
      if self.bool_spectra_exists: _spectra_group_t = list(self.ds[self.spectra_name].values)
    else: _list_t_turb = []
    for plt_filename in self.list_plt_filenames:
      t_turb = float(plt_filename.split("_")[-1]) / self.dict_sim_inputs["outputs_per_t_turb"]
      if (t_turb in _list_t_turb) and self.bool_spectra_exists: 
        index_t_turb = WWLists.getIndexClosestValue(_list_t_turb, t_turb)
        bool_array_missing = np.isnan(_spectra_group_t[index_t_turb][0])
        if not(bool_array_missing) and not(self.bool_recompute): continue
      self.list_t_turb.append(t_turb)
      spectrum_1d = self._computeDissipationFunctionSpectrum(plt_filename, self.cmap_t_turb(self.norm_t_turb(t_turb)))
      self.spectra_group_t.append(list(spectrum_1d))

  def _getCmap(self):
    list_t_turb = [
      float(plt_filename.split("_")[-1]) / self.dict_sim_inputs["outputs_per_t_turb"]
      for plt_filename in self.list_plt_filenames
    ]
    self.cmap_t_turb, self.norm_t_turb = PlotFuncs.createCmap(
      cmap_name = "viridis",
      vmin = np.min(list_t_turb),
      vmax = np.max(list_t_turb)
    )

  def _computeDissipationFunctionSpectrum(self, plt_filename, color):
    print("Reading velocity field data from:", plt_filename, flush=True)
    vfield_u = LoadData.loadFlashDataCube(
      filepath_file = f"{self.directory_plt}/{plt_filename}",
      num_blocks    = self.dict_sim_inputs["num_blocks"],
      num_procs     = self.dict_sim_inputs["num_procs"],
      field_name    = "vel",
    )
    print("Computing velocity gradient tensor...")
    r2tensor_gradj_ui = WWFields.vfieldGradient(vfield_u)
    sfield_div_u = np.einsum("iixyz->xyz", r2tensor_gradj_ui)
    r2tensor_bulk = 1/3 * np.einsum("xyz,ij->ijxyz", sfield_div_u, np.identity(3))
    ## S_ij = 0.5 ( \partial_i f_j + \partial_j f_i ) - 1/3 \delta_{ij} \partial_k f_k
    r2tensor_srt = 0.5 * (r2tensor_gradj_ui.transpose(1, 0, 2, 3, 4) + r2tensor_gradj_ui) - r2tensor_bulk
    ## \partial_j S_ij
    vfield_df = np.array([
      np.sum(WWFields.vfieldGradient(r2tensor_srt[:,0,:,:,:])[0], axis=0),
      np.sum(WWFields.vfieldGradient(r2tensor_srt[:,1,:,:,:])[1], axis=0),
      np.sum(WWFields.vfieldGradient(r2tensor_srt[:,2,:,:,:])[2], axis=0),
    ])
    print("Computing spectrum...")
    spectrum_3d = power_spectra_funcs.compute_tensor_power_spectrum(vfield_df)
    k_modes, spectrum_1d = power_spectra_funcs.spherical_integrate(spectrum_3d)
    del vfield_u, r2tensor_gradj_ui, sfield_div_u, r2tensor_bulk, r2tensor_srt, vfield_df
    spectrum_peak = np.argmax(spectrum_1d) + 1
    self.ax.plot(
      k_modes,
      spectrum_1d / np.sum(spectrum_1d),
      color=color, ls="-", lw=2, marker="o", ms=2, alpha=0.25
    )
    self.ax.axvline(x=spectrum_peak, color=color, ls="--", lw=1)
    print(" ")
    return spectrum_1d

  def saveFigure(self):
    self.ax.set_xscale("log")
    self.ax.set_yscale("log")
    self.ax.set_xlabel(r"$k$")
    PlotFuncs.addColorbar_fromCmap(
      fig            = self.fig,
      ax             = self.ax,
      cmap           = self.cmap_t_turb,
      norm           = self.norm_t_turb,
      orientation    = "horizontal",
      cbar_title     = r"$t / t_\mathrm{turb}$",
      cbar_title_pad = 10,
      fontsize       = 25,
      size           = 10
    )
    sim_name = FlashData.getSimName(self.dict_sim_inputs)
    fig_name = f"{sim_name}_{self.spectra_name}.png"
    PlotFuncs.saveFigure(self.fig, f"{self.directory_vis}/{fig_name}", bool_verbose=True)


## ###############################################################
## OPPERATOR HANDLING PLOT CALLS
## ###############################################################
def computeVelocityGradientTensorSpectrum(
    directory_sim, bool_save_data, bool_recompute,
    lock         = None,
    bool_verbose = True,
    **kwargs
  ):
  obj_plot_spectra = ComputeVelocityGradientTensorSpectrum(directory_sim, bool_recompute)
  obj_plot_spectra.performRoutines()
  if lock is not None: lock.acquire()
  if bool_save_data: obj_plot_spectra.saveFittedParams()
  obj_plot_spectra.saveFigure()
  if lock is not None: lock.release()
  if bool_verbose: WWTerminal.printLine(" ")


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  parser = WWArgparse.MyParser(description="Derive the velocity gradient tensor power spectrum from velocity field data.")
  args_opt = parser.add_argument_group(description="Optional processing arguments:")
  args_opt.add_argument("-sim_path", type=str, required=False, default=None, help="type: %(type)s")
  args_opt.add_argument("-save_data", default=False, **WWArgparse.OPT_BOOL_ARG)
  args_opt.add_argument("-recompute", default=False, **WWArgparse.OPT_BOOL_ARG)
  args = vars(parser.parse_args())
  directory_sim  = args["sim_path"]
  bool_save_data = args["save_data"]
  bool_recompute = args["recompute"]
  if directory_sim is None:
    FlashData.callFuncForAllSimulations(
      func = functools.partial(
        computeVelocityGradientTensorSpectrum,
        bool_save_data = BOOL_SAVE_DATA,
        bool_recompute = BOOL_RECOMPUTE
      ),
      bool_mproc         = BOOL_MPROC,
      list_base_paths    = LIST_BASE_PATHS,
      list_suite_folders = LIST_SUITE_FOLDERS,
      list_mach_folders  = LIST_MACH_FOLDERS,
      list_sim_folders   = LIST_SIM_FOLDERS,
      list_res_folders   = LIST_RES_FOLDERS
    )
  else:
    if not WWFnF.checkDirectoryExists(directory_sim): raise Exception("Directory does not exist.")
    computeVelocityGradientTensorSpectrum(
      directory_sim  = directory_sim,
      bool_save_data = bool_save_data,
      bool_recompute = bool_recompute
    )


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM