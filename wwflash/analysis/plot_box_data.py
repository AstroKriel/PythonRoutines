#!/bin/env python3


## ###############################################################
## MODULES
## ###############################################################
import os, sys, functools
import numpy as np

## 'tmpfile' needs to be loaded before any 'matplotlib' libraries,
## so matplotlib stores its cache in a temporary directory.
## (necessary when plotting in parallel)
import tempfile
os.environ["MPLCONFIGDIR"] = tempfile.mkdtemp()
import matplotlib.pyplot as plt
import matplotlib.colors as colors

## load user defined modules
from TheFlashModule import FileNames, FlashData, LoadData
from TheUsefulModule import WWFnF
from TheAnalysisModule import WWFields
from ThePlottingModule import PlotFuncs


## ###############################################################
## PREPARE WORKSPACE
## ###############################################################
plt.switch_backend("agg") # use a non-interactive plotting backend


## ###############################################################
## PROGRAM PARAMTERS
## ###############################################################
BOOL_MPROC = 0

LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/" ]
LIST_SUITE_FOLDERS = [ "Re50" ]
LIST_MACH_FOLDERS  = [ "Mach0.2" ]
LIST_SIM_FOLDERS   = [ "Pm5" ]
LIST_RES_FOLDERS   = [ "144" ]


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def fieldDivergence(field):
  num_dims = len(field)
  return np.ufunc.reduce(
    np.add, [
      np.gradient(field[dim], axis=dim)
      for dim in range(num_dims)
    ]
  )


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class PlotBoxData():
  def __init__(
      self,
      filepath_file, directory_vis, dict_sim_inputs,
      bool_verbose = True
    ):
    ## save input arguments
    self.filepath_file   = filepath_file
    self.directory_vis    = directory_vis
    self.dict_sim_inputs = dict_sim_inputs
    self.bool_verbose    = bool_verbose

  def performRoutine(self, lock):
    ## save figure
    if self.bool_verbose: print("Initialising figure...")
    self.fig_fields, self.axs_fields = plt.subplots(ncols=7, nrows=3, figsize=(6*5, 3*5.5))
    ## plot data
    self._plotMagneticField()
    # self._plotCurrent()
    # self._plotVelocityField()
    # self._plotDensityField()
    # self._plotKineticField()
    ## save figure
    if lock is not None: lock.acquire()
    sim_name = FlashData.getSimName(self.dict_sim_inputs)
    PlotFuncs.saveFigure(self.fig_fields, f"{self.directory_vis}/{sim_name}_field_slices.png", bool_draft=True)
    if lock is not None: lock.release()
    if self.bool_verbose: print(" ")

  def __plotScatterAgainstBField(self, fig, ax, field, cbar_title=None):
    PlotFuncs.plotScatter(
      fig               = fig,
      ax                = ax,
      list_x            = field[:,:,0].flatten(),
      list_y            = np.log10(self.mag_field_magn[:,:,0].flatten()),
      cbar_title        = cbar_title,
      bool_add_colorbar = True
    )

  def _plotMagneticField(self):
    if self.bool_verbose: print("Plotting magntic fields...")
    mag_field = LoadData.loadFlashDataCube(
      filepath_file = self.filepath_file,
      num_blocks    = self.dict_sim_inputs["num_blocks"],
      num_procs     = self.dict_sim_inputs["num_procs"],
      field_name    = "mag"
    )
    self.mag_field_magn = WWFields.vfieldMagnitude(mag_field)
    mag_field_rms       = WWFields.sfieldRMS(mag_field)
    # _, _, _, kappa      = WWFields.vfieldTNB(mag_field)
    PlotFuncs.plotScalarField(
      fig               = self.fig_fields,
      ax                = self.axs_fields[0][0],
      field_slice       = np.log10(self.mag_field_magn[:,:,0]**2 / mag_field_rms**2),
      cmap_name         = "cmr.iceburn",
      NormType          = functools.partial(PlotFuncs.MidpointNormalize, vmid=0),
      cbar_title        = r"$\log_{10}\big(b^2 / b_{\rm rms}^2\big)$",
      bool_add_colorbar = True
    )
    # PlotFuncs.plotScalarField(
    #   fig               = self.fig_fields,
    #   ax                = self.axs_fields[0][6],
    #   field_slice       = np.log10(kappa[0,:,:]),
    #   cmap_name         = "cmr.iceburn",
    #   NormType          = functools.partial(PlotFuncs.MidpointNormalize, vmid=0),
    #   cbar_title        = r"$\log_{10}\big(\kappa\big)$",
    #   bool_add_colorbar = True
    # )
    # x = np.linspace(-100, 100, 100)
    # # PlotFuncs.plotData_noAutoAxisScale(self.axs_fields[1][6], x, (-0.5*x - 7), ls=":", lw=2)
    # # self.__plotScatterAgainstBField(
    # #   fig        = self.fig_fields,
    # #   ax         = self.axs_fields[1][6],
    # #   field      = np.log10(kappa),
    # #   cbar_title = r"$\mathcal{P}(\kappa,b^2)$"
    # # )
    # # self.axs_fields[1][6].set_xlim([ -5, 10 ])
    # # self.axs_fields[1][6].set_ylim([ -20, 10 ])
    # self.axs_fields[2][6].set_xlabel(r"$\log_{10}\big(\kappa\big)$")

  def _plotCurrent(self):
    if self.bool_verbose: print("Plotting current density...")
    cur_field_x, cur_field_y, cur_field_z = LoadData.loadFlashDataCube(
      filepath_file = self.filepath_file,
      num_blocks    = self.dict_sim_inputs["num_blocks"],
      num_procs     = self.dict_sim_inputs["num_procs"],
      field_name    = "cur"
    )
    cur_field_magn = np.sqrt(cur_field_x**2 + cur_field_y**2 + cur_field_z**2)
    cur_rms = np.sqrt(np.mean(cur_field_x**2 + cur_field_y**2 + cur_field_z**2))
    PlotFuncs.plotScalarField(
      fig               = self.fig_fields,
      ax                = self.axs_fields[0][1],
      field_slice       = np.log10(cur_field_magn[:,:,0]**2 / cur_rms**2),
      cmap_name         = "cmr.watermelon",
      NormType          = functools.partial(PlotFuncs.MidpointNormalize, vmid=0),
      cbar_title        = r"$\log_{10}\big(j^2 / j_{\rm rms}^2\big)$",
      bool_add_colorbar = True
    )
    x = np.linspace(-100, 100, 100)
    # PlotFuncs.plotData_noAutoAxisScale(self.axs_fields[1][1], x, x, ls=":", lw=2)
    # self.__plotScatterAgainstBField(
    #   fig        = self.fig_fields,
    #   ax         = self.axs_fields[1][1],
    #   field      = np.log10(cur_field_magn),
    #   cbar_title = r"$\mathcal{P}(j^2,b^2)$"
    # )
    # self.axs_fields[1][1].set_xlim([ -20, 10 ])
    # self.axs_fields[1][1].set_ylim([ -20, 10 ])
    self.axs_fields[2][1].set_xlabel(r"$\log_{10}\big(j^2\big)$")

  def _plotVelocityField(self):
    if self.bool_verbose: print("Plotting velocity fields...")
    ## plot velocity field
    vel_field_x, vel_field_y, vel_field_z = LoadData.loadFlashDataCube(
      filepath_file = self.filepath_file,
      num_blocks    = self.dict_sim_inputs["num_blocks"],
      num_procs     = self.dict_sim_inputs["num_procs"],
      field_name    = "vel",
    )
    self.vel_field_magn = np.sqrt(vel_field_x**2 + vel_field_y**2 + vel_field_z**2)
    vel_rms = np.sqrt(np.mean(vel_field_x**2 + vel_field_y**2 + vel_field_z**2))
    PlotFuncs.plotScalarField(
      fig               = self.fig_fields,
      ax                = self.axs_fields[0][2],
      field_slice       = np.log10(self.vel_field_magn[:,:,0]**2 / vel_rms**2),
      cmap_name         = "cmr.viola",
      NormType          = functools.partial(PlotFuncs.MidpointNormalize, vmid=0),
      cbar_title        = r"$\log_{10}\big(u^2 / u_{\rm rms}^2\big)$",
      bool_add_colorbar = True
    )
    x = np.linspace(-100, 100, 100)
    # PlotFuncs.plotData_noAutoAxisScale(self.axs_fields[1][2], x, x, ls=":", lw=2)
    # self.__plotScatterAgainstBField(
    #   fig        = self.fig_fields,
    #   ax         = self.axs_fields[1][2],
    #   field      = np.log10(self.vel_field_magn),
    #   cbar_title = r"$\mathcal{P}(u^2,b^2)$"
    # )
    # self.axs_fields[1][2].set_xlim([ -10, 10 ])
    # self.axs_fields[1][2].set_ylim([ -20, 10 ])
    self.axs_fields[2][2].set_xlabel(r"$\log_{10}\big(u^2\big)$")
    ## plot fieldDivergence of velocity field
    vel_field_fieldDivergence = fieldDivergence([ vel_field_x, vel_field_y, vel_field_z ])
    PlotFuncs.plotScalarField(
      fig               = self.fig_fields,
      ax                = self.axs_fields[0][3],
      field_slice       = vel_field_fieldDivergence[:,:,0],
      cmap_name         = "cmr.viola",
      NormType          = functools.partial(PlotFuncs.MidpointNormalize, vmid=0),
      cbar_title        = r"$\nabla\cdot\vec{u}$",
      bool_add_colorbar = True
    )
    # self.__plotScatterAgainstBField(
    #   fig        = self.fig_fields,
    #   ax         = self.axs_fields[1][3],
    #   field      = vel_field_fieldDivergence, 
    #   cbar_title = r"$\mathcal{P}(\nabla\cdot\vec{u},b^2)$"
    # )
    # self.axs_fields[1][3].set_xlim([ -15, 15 ])
    # self.axs_fields[1][3].set_ylim([ -20, 10 ])
    self.axs_fields[2][3].set_xlabel(r"$\nabla\cdot\vec{u}$")

  def _plotDensityField(self):
    if self.bool_verbose: print("Plotting density field...")
    self.dens_field = LoadData.loadFlashDataCube(
      filepath_file = self.filepath_file,
      num_blocks    = self.dict_sim_inputs["num_blocks"],
      num_procs     = self.dict_sim_inputs["num_procs"],
      field_name    = "dens"
    )
    PlotFuncs.plotScalarField(
      fig               = self.fig_fields,
      ax                = self.axs_fields[0][4],
      field_slice       = np.log10(self.dens_field[:,:,0]),
      cmap_name         = "cmr.seasons",
      NormType          = colors.Normalize,
      cbar_title        = r"$\log_{10}\big(\rho\big)$",
      bool_add_colorbar = True
    )
    x = np.linspace(-100, 100, 100)
    # PlotFuncs.plotData_noAutoAxisScale(self.axs_fields[1][4], x, x, ls=":", lw=2)
    # self.__plotScatterAgainstBField(
    #   fig        = self.fig_fields,
    #   ax         = self.axs_fields[1][4],
    #   field      = np.log10(self.dens_field),
    #   cbar_title = r"$\mathcal{P}(\rho^2,b^2)$"
    # )
    # self.axs_fields[1][4].set_xlim([ -20, 10 ])
    # self.axs_fields[1][4].set_ylim([ -20, 10 ])
    self.axs_fields[2][4].set_xlabel(r"$\log_{10}\big(\rho^2\big)$")

  def _plotKineticField(self):
    if self.bool_verbose: print("Plotting kinetic field...")
    kin_field = self.dens_field * self.vel_field_magn**2
    PlotFuncs.plotScalarField(
      fig               = self.fig_fields,
      ax                = self.axs_fields[0][5],
      field_slice       = np.log10(kin_field[:,:,0]),
      cmap_name         = "plasma",
      NormType          = colors.Normalize,
      cbar_title        = r"$\log_{10}\big(\rho u^2\big)$",
      bool_add_colorbar = True
    )
    x = np.linspace(-100, 100, 100)
    # PlotFuncs.plotData_noAutoAxisScale(self.axs_fields[1][5], x, x, ls=":", lw=2)
    # self.__plotScatterAgainstBField(
    #   fig        = self.fig_fields,
    #   ax         = self.axs_fields[1][5],
    #   field      = np.log10(kin_field),
    #   cbar_title = r"$\mathcal{P}(\rho u^2,b^2)$"
    # )
    # self.axs_fields[1][5].set_xlim([ -20, 10 ])
    # self.axs_fields[1][5].set_ylim([ -20, 10 ])
    self.axs_fields[2][5].set_xlabel(r"$\log_{10}\big(\rho u^2\big)$")


## ###############################################################
## OPPERATOR HANDLING PLOT CALLS
## ###############################################################
def plotSimData(directory_sim, bool_verbose=True, lock=None, **kwargs):
  ## read simulation input parameters
  dict_sim_inputs = FlashData.readSimInputs(directory_sim, bool_verbose)
  filename        = FileNames.FILENAME_FLASH_PLT_FILES + str(500).zfill(4)
  filepath_file   = f"{directory_sim}/plt/{filename}"
  print("Looking at:", filepath_file)
  ## make sure a visualisation folder exists
  directory_vis = f"{directory_sim}/vis_folder/"
  WWFnF.createDirectory(directory_vis, bool_verbose=False)
  ## plot quantities
  obj_plot_box = PlotBoxData(
    filepath_file   = filepath_file,
    directory_vis   = directory_vis,
    dict_sim_inputs = dict_sim_inputs,
    bool_verbose    = bool_verbose
  )
  obj_plot_box.performRoutine(lock)


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  FlashData.callFuncForAllSimulations(
    func               = plotSimData,
    bool_mproc         = BOOL_MPROC,
    list_base_paths    = LIST_BASE_PATHS,
    list_suite_folders = LIST_SUITE_FOLDERS,
    list_mach_folders  = LIST_MACH_FOLDERS,
    list_sim_folders   = LIST_SIM_FOLDERS,
    list_res_folders   = LIST_RES_FOLDERS
  )


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM