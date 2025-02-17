## ###############################################################
## MODULES
## ###############################################################
import os, sys
import numpy as np

from scipy import interpolate, ndimage

## 'tmpfile' needs to be loaded before any 'matplotlib' libraries,
## so matplotlib stores its cache in a temporary directory.
## (necessary when plotting in parallel)
import tempfile
os.environ["MPLCONFIGDIR"] = tempfile.mkdtemp()

import matplotlib.pyplot as plt

## load user defined modules
from Loki.TheFlashModule import FlashData, LoadData
from Loki.TheUsefulModule import WWFnF, WWArgparse, WWLists
from Loki.ThePlottingModule import PlotFuncs


## ###############################################################
## PREPARE WORKSPACE
## ###############################################################
plt.switch_backend("agg") # use a non-interactive plotting backend


## ###############################################################
## PROGRAM PARAMTERS
## ###############################################################
BOOL_MPROC = 1

LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/" ]
LIST_SUITE_FOLDERS = [ "Re500" ]
LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach0.5", "Mach1", "Mach2", "Mach5", "Mach10" ]
LIST_SIM_FOLDERS   = [ "Pm1" ]
LIST_RES_FOLDERS   = [ "288" ]
LIST_SIM_NAMES     = [  ]


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def computeDerivative(x, y):
  delta_x = x[1] - x[0] # assumes uniform spacing
  dy_dx = [
    (y[i+1] - y[i-1]) / (2 * delta_x)
    for i in range(1, len(x)-1)
  ]
  return x[1:-1], dy_dx

def plotLine(
    ax, domain, y_int, slope,
    color  = "black",
    ls     = "-",
    lw     = 2.0,
    zorder = 10
  ):
  x = np.linspace(domain[0], domain[1], 100)
  y = y_int + slope * x
  PlotFuncs.plotData_noAutoAxisScale(ax, x, y, ls=ls, lw=lw, color=color, zorder=zorder)

def plotLinePassingThroughPoint(
    ax, domain, slope, coord,
    color  = "black",
    ls     = "-",
    lw     = 2.0,
    zorder = 10
  ):
  x_coord, y_coord = coord
  y_int = y_coord - slope * x_coord
  plotLine(ax, domain, y_int, slope, color, ls, lw, zorder)


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class PlotTurbData():
  def __init__(
      self,
      fig, axs, directory_sim, dict_sim_inputs,
      dict_sim_summary = None,
      bool_verbose     = True
    ):
    ## save input arguments
    self.fig              = fig
    self.axs              = axs
    self.directory_sim    = directory_sim
    self.dict_sim_inputs  = dict_sim_inputs
    self.dict_sim_summary = dict_sim_summary
    self.bool_verbose     = bool_verbose

  def performRoutines(self):
    if self.bool_verbose: print("Loading volume integrated quantities...")
    self._loadData()
    if self.bool_verbose: print("Plotting volume integrated quantities...")
    self._plotMach()
    self._plotEnergyRatio()
    if len(self.axs) > 2: self._plotDtEmag()
    self._labelPlots()

  def _loadData(self):
    ## load Mach data
    _, data_Mach = LoadData.loadVIData(
      directory  = self.directory_sim,
      field_name = "mach",
      t_turb     = self.dict_sim_inputs["t_turb"],
      time_start = 0.0,
      time_end   = np.inf
    )
    ## load kinetic energy
    _, data_Ekin = LoadData.loadVIData(
      directory  = self.directory_sim,
      field_name = "kin",
      t_turb     = self.dict_sim_inputs["t_turb"],
      time_start = 0.0,
      time_end   = np.inf
    )
    ## load magnetic energy
    data_time, data_Emag = LoadData.loadVIData(
      directory  = self.directory_sim,
      field_name = "mag",
      t_turb     = self.dict_sim_inputs["t_turb"],
      time_start = 0.0,
      time_end   = np.inf
    )
    ## Only relevant when loading data while the simulation is running.
    ## Only grab the portion of data where all quantities have been sefely written.
    max_len = min([
      len(data_time),
      len(data_Mach),
      len(data_Ekin),
      len(data_Emag)
    ])
    ## save data
    self.data_time = data_time[1:max_len]
    self.data_Mach = data_Mach[1:max_len]
    self.data_Emag = data_Emag[1:max_len]
    self.data_Ekin = data_Ekin[1:max_len]
    if self.data_Emag[-1] < 1e-9: print(f"WARNING: Magnetic energy is zero: {self.directory_sim}")
    if self.data_Ekin[-1] < 1e-9: print(f"WARNING: Kinetic energy is zero: {self.directory_sim}")
    ## compute and save energy ratio: 'mag_energy / kin_energy'
    self.data_Eratio = [
      mag_energy / kin_energy
      for mag_energy, kin_energy in zip(
        self.data_Emag,
        self.data_Ekin
      )
    ]
    ## define plot domain
    self.max_time = 1.1 * max([ 100, max(self.data_time) ])

  def _plotMach(self):
    self.axs[0].plot(
      self.data_time,
      self.data_Mach,
      color="orange", ls="-", lw=1.5, zorder=3
    )
    self.axs[0].set_ylabel(r"$\mathcal{M}$")
  
  def _plotEnergyRatio(self):
    self.axs[1].plot(
      self.data_time,
      np.log(self.data_Eratio),
      color="orange", ls="-", lw=1.5, zorder=3
    )
    self.axs[1].set_ylabel(r"$\ln(E_\mathrm{mag} / E_\mathrm{kin})$")
  
  def _plotDtEmag(self):
    if len(self.axs) < 3: return
    sampled_time = np.linspace(np.min(self.data_time), np.max(self.data_time), 100)
    spline_obj_ln_Emag = interpolate.CubicSpline(self.data_time, np.log(self.data_Emag))
    sampled_ln_Emag = spline_obj_ln_Emag(sampled_time)
    dx1, d1_ln_Emag = computeDerivative(sampled_time, sampled_ln_Emag)
    d1_ln_Emag_smoothed = ndimage.gaussian_filter1d(d1_ln_Emag, sigma=3)
    self.axs[2].axhline(0.0, color="black", ls="--")
    self.axs[2].plot(dx1, d1_ln_Emag, ls="-", color="orange", alpha=0.5)
    self.axs[2].plot(dx1, d1_ln_Emag_smoothed, ls="-", color="black")
    self.axs[2].set_ylabel(r"$\frac{d}{dt} \ln(E_\mathrm{mag})$")
    y_min = np.min([ -0.1, 1.1 * np.min(d1_ln_Emag_smoothed) ])
    y_max = np.max([  0.1, 1.1 * np.max(d1_ln_Emag_smoothed) ])
    self.axs[2].set_ylim([ y_min, y_max ])

  def _labelPlots(self):
    for ax in self.axs: ax.set_xlim([ -5, self.max_time ])
    self.axs[len(self.axs)-1].set_xlabel(r"$t / t_\mathrm{turb}$")
    FlashData.addLabel_simInputs(
      fig             = self.fig,
      ax              = self.axs[1],
      dict_sim_inputs = self.dict_sim_inputs,
      bbox            = (1, 0),
      vpos            = (0.95, 0.05),
      bool_show_res   = True
    )
    if self.dict_sim_summary is not None:
      try:
        time_linear_start = self.dict_sim_summary["nl_regime"]["start_time"]
        time_linear_end   = self.dict_sim_summary["nl_regime"]["end_time"]
        exp_gamma_ave     = self.dict_sim_summary["exp_regime"]["growth_rate"]["ave"]
        index_exp_start   = WWLists.getIndexClosestValue(self.data_time, 5)
        index_exp_end     = WWLists.getIndexClosestValue(self.data_time, time_linear_start)
        sat_Eratio_ave    = self.dict_sim_summary["sat_regime"]["E_ratio"]["ave"]
        self.axs[1].axhline(np.log(sat_Eratio_ave), color="black", ls="--", lw=1.0, zorder=1)
        plotLinePassingThroughPoint(
          ax     = self.axs[1],
          domain = (-20, self.max_time),
          slope  = exp_gamma_ave,
          coord  = (
            np.mean([5, time_linear_start]),
            0.9*np.mean(np.log(self.data_Eratio[index_exp_start : index_exp_end]))
          ),
          color  = "black",
          ls     = "--",
          lw     = 1.0,
          zorder = 1
        )
        for ax in self.axs:
          ax.axvline(x=time_linear_start, ls="--", color="black", lw=1.0, zorder=1)
          ax.axvline(x=time_linear_end,   ls="--", color="black", lw=1.0, zorder=1)
          ax.axvspan(time_linear_start, time_linear_end, color="grey", alpha=0.5, zorder=2 )
      except KeyError: pass


## ###############################################################
## OPPERATOR HANDLING PLOT CALLS
## ###############################################################
def plotSimData(
    directory_sim,
    lock         = None,
    bool_verbose = True,
    bool_force   = False,
    **kwargs
  ):
  ## read simulation input parameters
  dict_sim_inputs = FlashData.readSimInputs(directory_sim, bool_verbose=False)
  if not(bool_force) and (len(LIST_SIM_NAMES) > 0):
    sim_name = FlashData.getSimName(dict_sim_inputs)
    if not(sim_name in LIST_SIM_NAMES): return
  print("Looking at:", directory_sim)
  try:
    dict_sim_summary = FlashData.readSimSummary(directory_sim, bool_verbose)
  except: dict_sim_summary = None
  ## make sure a visualisation folder exists
  directory_vis = f"{directory_sim}/vis_folder/"
  WWFnF.createDirectory(directory_vis, bool_verbose=False)
  ## INITIALISE FIGURE
  ## -----------------
  if bool_verbose: print("Initialising figure...")
  fig, fig_grid = PlotFuncs.createFigure_grid(
    fig_scale        = 1.0,
    fig_aspect_ratio = (5.0, 8.0),
    num_rows         = 3,
    num_cols         = 2
  )
  ax_Mach    = fig.add_subplot(fig_grid[0, 0])
  ax_Eratio  = fig.add_subplot(fig_grid[1, 0])
  ax_Dt_Emag = fig.add_subplot(fig_grid[2, 0])
  ## PLOT INTEGRATED QUANTITIES
  ## --------------------------
  obj_plot_turb = PlotTurbData(
    fig              = fig,
    axs              = [ ax_Mach, ax_Eratio, ax_Dt_Emag ],
    directory_sim = directory_sim,
    dict_sim_inputs  = dict_sim_inputs,
    dict_sim_summary = dict_sim_summary,
    bool_verbose     = bool_verbose
  )
  obj_plot_turb.performRoutines()
  ## SAVE FIGURE + DATASET
  ## ---------------------
  if lock is not None: lock.acquire()
  sim_name = FlashData.getSimName(dict_sim_inputs)
  fig_name = f"{sim_name}_time_evolution.png"
  PlotFuncs.saveFigure(fig, f"{directory_vis}/{fig_name}", bool_verbose=True)
  if lock is not None: lock.release()
  if bool_verbose: print(" ")


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  parser = WWArgparse.MyParser(description="Calculate kinetic and magnetic energy spectra.")
  args_opt = parser.add_argument_group(description="Optional processing arguments:")
  args_opt.add_argument("-sim_path", type=str, required=False, default=None, help="type: %(type)s")
  args = vars(parser.parse_args())
  directory_sim = args["sim_path"]
  if directory_sim is None:
    FlashData.callFuncForAllSimulations(
      func               = plotSimData,
      bool_mproc         = BOOL_MPROC,
      list_base_paths    = LIST_BASE_PATHS,
      list_suite_folders = LIST_SUITE_FOLDERS,
      list_mach_folders  = LIST_MACH_FOLDERS,
      list_sim_folders   = LIST_SIM_FOLDERS,
      list_res_folders   = LIST_RES_FOLDERS
    )
  else:
    if WWFnF.checkDirectoryExists(directory_sim): plotSimData(directory_sim, bool_force=True)
    else: raise Exception("Directory does not exist.")


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM