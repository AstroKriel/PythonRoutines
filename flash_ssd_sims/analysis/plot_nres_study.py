## ###############################################################
## MODULES
## ###############################################################
import os, sys, copy
import numpy as np
import matplotlib.pyplot as plt

from scipy.optimize import curve_fit

## load user defined modules
from TheFlashModule import FlashData, FileNames
from TheUsefulModule import WWFnF, WWObjs
from TheFittingModule import UserModels
from ThePlottingModule import PlotFuncs


## ###############################################################
## PREPARE WORKSPACE
## ###############################################################
plt.switch_backend("agg") # use a non-interactive plotting backend


## ###############################################################
## PROGRAM PARAMETERS
## ###############################################################
BOOL_DEBUG_MODE = 0
BOOL_MPROC      = 1

# LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/", "/scratch/ek9/nk7952/" ]
# LIST_SUITE_FOLDERS = [ "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm2" ]
# LIST_RES_FOLDERS   = [ "18", "36", "72", "144", "288", "576", "1152" ]

## full set of simulations
LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/", "/scratch/ek9/nk7952/" ]
LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
LIST_RES_FOLDERS   = [ "18", "36", "72", "144", "288", "576", "1152" ]



## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def createLabel_logisticModel(stats):
  return r"${} \pm {}$\;".format(
    str(round(stats[0], 2)),
    str(round(stats[1], 2))
  )

def createLabel_powerLaw(stats):
  return r"${} k^{}$\;".format(
    str(round(stats[0], 2)),
    "{" + str(round(stats[1], 2)) + "}"
  )

def check_mean_within_10_percent(list_vals):
  list_log_vals = np.log10(list_vals)
  list_abs_diffs = np.abs(list_log_vals[-1] - list_log_vals[:-1])
  return np.all(list_abs_diffs < 0.1) # check if all absolute differences are less than or equal to 0.1

def fitLogisticModel(
    list_x, list_y_ave_group_x, list_y_std_group_x,
    ax     = None,
    color  = "black",
    ls     = ":",
    bounds = ( (1e-2, 1e-1, 0.0), (5e2, 1e4, 5.0) ) # amplitude, turnover scale, turnover rate
  ):
  ## check if measured scales increase or decrease with resolution
  if list_y_ave_group_x[0] <= list_y_ave_group_x[-1]:
    func = UserModels.ListOfModels.logistic_growth_increasing
  else: func = UserModels.ListOfModels.logistic_growth_decreasing
  fit_params, fit_cov = curve_fit(
    f     = func,
    xdata = list_x,
    ydata = list_y_ave_group_x,
    sigma = None if (list_y_std_group_x[0] is None) else list_y_std_group_x,
    absolute_sigma=True, bounds=bounds, maxfev=10**5
  )
  fit_std = np.mean(list_y_std_group_x) if list_y_std_group_x[0] is not None else None
  # fit_std = np.sqrt(np.diag(fit_cov))[0] # confidence in fit
  data_x  = np.logspace(np.log10(1), np.log10(10**4), 100)
  data_y  = func(data_x, *fit_params)
  ax.axhline(y=fit_params[0], ls="--", color="red")
  ax.axvline(x=fit_params[1], ls="--", color="red")
  if ax is not None: ax.plot(data_x, data_y, color=color, ls=ls, lw=1.5)
  return {
    "val" : fit_params[0],
    "std" : fit_std
  }

def fitScales(ax, dict_scale, ssd_regime, str_quantity, bool_extend=True, color="black"):
  if dict_scale is None: return
  list_x = [
    int(res_folder)
    for res_folder in dict_scale.keys()
    if ("i" not in res_folder)
  ]
  list_y_ave_group_x = [
    dict_scale[str(nres)][ssd_regime][str_quantity]["ave"]
    for nres in list_x
  ]
  list_y_std_group_x = [
    dict_scale[str(nres)][ssd_regime][str_quantity]["std"]
    if (dict_scale[str(nres)][ssd_regime][str_quantity]["std"] is not None) else
    0
    for nres in list_x
  ]
  list_y_std_group_x = [
    val
    if (val > 0) else
    None
    for val in list_y_std_group_x
  ]
  if bool_extend:
    list_x.append(2 * list_x[-1])
    list_y_ave_group_x.append(list_y_ave_group_x[-1])
    list_y_std_group_x.append(list_y_std_group_x[-1])
  ## subset for data that should be fitted
  list_good_indices = [
    list_y_ave_group_x[idx] is not None
    for idx in range(len(list_x))
  ]
  list_x_sub = [ list_x[idx] for idx in range(len(list_x)) if list_good_indices[idx] ]
  list_y_ave_group_x_sub = [ list_y_ave_group_x[idx] for idx in range(len(list_x)) if list_good_indices[idx] ]
  list_y_std_group_x_sub = [ list_y_std_group_x[idx] for idx in range(len(list_x)) if list_good_indices[idx] ]
  ## fit measured scales at different resolution runs
  dict_stats = {
    "val" : list_y_ave_group_x_sub[-1],
    "std" : list_y_std_group_x_sub[-1]
  }
  if check_mean_within_10_percent(list_y_ave_group_x_sub) or (len(list_x_sub) <= 4):
    ax.axhline(y=dict_stats["val"], color="blue", ls="--", lw=1.5)
  else:
    try:
      dict_stats = fitLogisticModel(
        ax                 = ax,
        list_x             = list_x_sub,
        list_y_ave_group_x = list_y_ave_group_x_sub,
        list_y_std_group_x = list_y_std_group_x_sub,
        color              = color,
        ls                 = ":"
      )
    except: print("oops")
  if "inf" not in dict_scale: dict_scale["inf"] = {}
  if ssd_regime not in dict_scale["inf"]: dict_scale["inf"][ssd_regime] = {}
  dict_scale["inf"][ssd_regime][str_quantity] = {
    "ave" : dict_stats["val"],
    "std" : dict_stats["std"],
  }

## ###############################################################
## OPERATOR CLASS
## ###############################################################
class PlotConvergence():
  def __init__(self, directory_sim_288):
    self.dict_sim_inputs = FlashData.readSimInputs(directory_sim_288, bool_verbose=False)
    self.sim_name        = FlashData.getSimName(self.dict_sim_inputs, bool_include_res=False)
    suite_folder         = self.dict_sim_inputs["suite_folder"]
    mach_folder          = self.dict_sim_inputs["mach_folder"]
    sim_folder           = self.dict_sim_inputs["sim_folder"]
    self.directory_base  = f"/scratch/jh2/nk7952/{suite_folder}/{mach_folder}/{sim_folder}/"
    self.directory_Nres576 = f"/scratch/ek9/nk7952/{suite_folder}/{mach_folder}/{sim_folder}/576/"
    directory_vis        = f"{self.directory_base}/vis_folder/"
    WWFnF.createDirectory(directory_vis, bool_verbose=False)
    self.filepath_fig = f"{directory_vis}/{self.sim_name}_nres.png"

  def performRoutine(self):
    self._readData()
    num_rows = 5
    num_cols = 2
    self.fig, fig_grid = PlotFuncs.createFigure_grid(
      fig_scale        = 0.85,
      fig_aspect_ratio = (5.0, 8.0),
      num_rows         = num_rows,
      num_cols         = num_cols,
    )
    self.dict_k_nu_reyh = {}
    self.dict_k_nu_srt  = {}
    self.dict_k_ch      = {}
    self.dict_k_eta     = {}
    self.dict_k_p       = {}
    for col_index, ssd_regime in enumerate([ "exp_regime", "sat_regime" ]):
      self.ax_k_nu_reyh   = self.fig.add_subplot((fig_grid[0,col_index]))
      self.ax_k_nu_srt    = self.fig.add_subplot((fig_grid[1,col_index]))
      self.ax_k_ch        = self.fig.add_subplot((fig_grid[2,col_index]))
      self.ax_k_eta       = self.fig.add_subplot((fig_grid[3,col_index]))
      self.ax_k_p         = self.fig.add_subplot((fig_grid[4,col_index]))
      self._plotData(ssd_regime)
      self._fitScales(ssd_regime)
      self._labelFigure()

  def saveData(self):
    dict_stats_nres = {
      "k_nu_reyh" : self.dict_k_nu_reyh,
      "k_nu_srt"  : self.dict_k_nu_srt,
      "k_ch"      : self.dict_k_ch,
      "k_eta"     : self.dict_k_eta,
      "k_p"       : self.dict_k_p,
    }
    WWObjs.saveDict2JsonFile(
      filepath_file = f"{self.directory_base}/{FileNames.FILENAME_NRES_SUMMARY}",
      input_dict    = dict_stats_nres,
    )

  def saveFigure(self):
    PlotFuncs.saveFigure(self.fig, self.filepath_fig)

  def _readData(self):
    self.list_res_folders = []
    self.dict_res_data    = {}
    for res_folder in LIST_RES_FOLDERS:
      if res_folder == "576":
        directory_sim = self.directory_Nres576
      else: directory_sim = f"{self.directory_base}/{res_folder}/"
      if not WWFnF.checkDirectoryExists(directory_sim): continue
      dict_sim_summary = FlashData.readSimSummary(directory_sim)
      if not(dict_sim_summary["bool_SSD_growth"]): continue
      self.dict_res_data[res_folder] = dict_sim_summary
      self.list_res_folders.append(res_folder)
  
  def _plotErrorBar_1D(self, ax, res_folder, ssd_regime, str_quantity, dict_scale=None, str_ave="ave", str_std="std"):
    y_ave = self.dict_res_data.get(res_folder, {}).get(ssd_regime, {}).get(str_quantity, {}).get(str_ave, None)
    y_std = self.dict_res_data.get(res_folder, {}).get(ssd_regime, {}).get(str_quantity, {}).get(str_std, None)
    ax.errorbar(int(res_folder), y_ave, yerr=y_std, fmt="o", color="black", lw=1.5)
    if dict_scale is not None:
      if res_folder not in dict_scale: dict_scale[res_folder] = {}
      if ssd_regime not in dict_scale[res_folder]: dict_scale[res_folder][ssd_regime] = {}
      dict_scale[res_folder][ssd_regime][str_quantity] = {
        "ave" : y_ave,
        "std" : y_std,
      }

  def _plotData(self, ssd_regime):
    for res_folder in self.list_res_folders:
      self._plotErrorBar_1D(
        ax           = self.ax_k_nu_reyh,
        res_folder   = res_folder,
        ssd_regime   = ssd_regime,
        str_quantity = "k_nu_reyh",
        dict_scale   = self.dict_k_nu_reyh,
      )
      self._plotErrorBar_1D(
        ax           = self.ax_k_nu_srt,
        res_folder   = res_folder,
        ssd_regime   = ssd_regime,
        str_quantity = "k_nu_srt",
        dict_scale   = self.dict_k_nu_srt,
      )
      self._plotErrorBar_1D(
        ax           = self.ax_k_ch,
        res_folder   = res_folder,
        ssd_regime   = ssd_regime,
        str_quantity = "k_ch",
        dict_scale   = self.dict_k_ch,
      )
      self._plotErrorBar_1D(
        ax           = self.ax_k_eta,
        res_folder   = res_folder,
        ssd_regime   = ssd_regime,
        str_quantity = "k_eta",
        dict_scale   = self.dict_k_eta,
      )
      self._plotErrorBar_1D(
        ax           = self.ax_k_p,
        res_folder   = res_folder,
        ssd_regime   = ssd_regime,
        str_quantity = "k_p",
        dict_scale   = self.dict_k_p,
      )

  def _fitScales(self, ssd_regime):
    fitScales(
      ax           = self.ax_k_nu_reyh,
      dict_scale   = self.dict_k_nu_reyh,
      ssd_regime   = ssd_regime,
      str_quantity = "k_nu_reyh",
    )
    fitScales(
      ax           = self.ax_k_nu_srt,
      dict_scale   = self.dict_k_nu_srt,
      ssd_regime   = ssd_regime,
      str_quantity = "k_nu_srt",
    )
    fitScales(
      ax           = self.ax_k_ch,
      dict_scale   = self.dict_k_ch,
      ssd_regime   = ssd_regime,
      str_quantity = "k_ch",
    )
    fitScales(
      ax           = self.ax_k_eta,
      dict_scale   = self.dict_k_eta,
      ssd_regime   = ssd_regime,
      str_quantity = "k_eta",
    )
    fitScales(
      ax           = self.ax_k_p,
      dict_scale   = self.dict_k_p,
      ssd_regime   = ssd_regime,
      str_quantity = "k_p",
    )

  def _labelFigure(self):
    ## define helper variables
    list_axs = [
      self.ax_k_nu_reyh,
      self.ax_k_nu_srt,
      self.ax_k_ch,
      self.ax_k_eta,
      self.ax_k_p,
    ]
    ## adjust axis
    for ax_index in range(len(list_axs)):
      list_axs[ax_index].set_xscale("log")
      list_axs[ax_index].set_yscale("log")
    ## label x-axis
    list_axs[-1].set_xlabel(r"$N_{\rm res}$")
    ## label y-axis
    self.ax_k_nu_reyh.set_ylabel(r"$k_{\nu, \mathrm{Re}}$")
    self.ax_k_nu_srt.set_ylabel(r"$k_{\nu, \mathrm{SRT}}$")
    self.ax_k_ch.set_ylabel(r"$k_\mathrm{CH}$")
    self.ax_k_eta.set_ylabel(r"$k_{\eta}$")
    self.ax_k_p.set_ylabel(r"$k_\mathrm{p}$")
    ## annotate simulation parameters
    FlashData.addLabel_simInputs(
      fig             = self.fig,
      ax              = list_axs[0],
      dict_sim_inputs = self.dict_sim_inputs,
      bbox            = (1.0, 0.0),
      vpos            = (0.95, 0.05),
      bool_show_res   = False
    )


## ###############################################################
## OPPERATOR HANDLING PLOT CALLS
## ###############################################################
def plotSimData(
    directory_sim,
    lock            = None,
    bool_debug_mode = False,
    bool_verbose    = True,
    **kwargs
  ):
  print("Looking at:", directory_sim)
  obj = PlotConvergence(directory_sim_288=directory_sim)
  obj.performRoutine()
  ## SAVE FIGURE + DATASET
  ## ---------------------
  if lock is not None: lock.acquire()
  if not(bool_debug_mode): obj.saveData()
  obj.saveFigure()
  if lock is not None: lock.release()
  if bool_verbose: print(" ")


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  FlashData.callFuncForAllSimulations(
    func               = plotSimData,
    bool_mproc         = BOOL_MPROC,
    bool_debug_mode    = BOOL_DEBUG_MODE,
    list_base_paths    = LIST_BASE_PATHS,
    list_suite_folders = LIST_SUITE_FOLDERS,
    list_mach_folders  = LIST_MACH_FOLDERS,
    list_sim_folders   = LIST_SIM_FOLDERS,
    list_res_folders   = [ "288" ]
  )


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM