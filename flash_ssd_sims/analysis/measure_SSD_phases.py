## ###############################################################
## MODULES
## ###############################################################
import os, sys, functools
import numpy as np

from scipy import interpolate, ndimage

## 'tmpfile' needs to be loaded before any 'matplotlib' libraries,
## so matplotlib stores its cache in a temporary directory.
## (necessary when plotting in parallel)
import tempfile
os.environ["MPLCONFIGDIR"] = tempfile.mkdtemp()
import matplotlib.pyplot as plt

## load user defined modules
from Loki.TheFlashModule import FlashData, LoadData, FileNames
from Loki.TheUsefulModule import WWFnF, WWObjs, WWArgparse
from Loki.ThePlottingModule import PlotFuncs
from Loki.TheFittingModule import FitFuncs


## ###############################################################
## PREPARE WORKSPACE
## ###############################################################
plt.switch_backend("agg") # use a non-interactive plotting backend


## ###############################################################
## PROGRAM PARAMTERS
## ###############################################################
BOOL_SAVE_DATA = 0

# ## subset of simulations
# BOOL_MPROC         = 0
# LIST_BASE_PATHS    = [ "/scratch/ek9/nk7952/" ]
# LIST_SUITE_FOLDERS = [ "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
# LIST_RES_FOLDERS   = [ "576" ]

# ## full list of simulations
# BOOL_MPROC         = 1
# LIST_BASE_PATHS    = [ "/scratch/jh2/nk7952/" ]
# LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm1000", "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
# LIST_RES_FOLDERS   = [ "18", "36", "72", "144", "288", "576", "1152" ]

LIST_SIM_NAMES = [ ]


## ###############################################################
## HELPER FUNCATIONS
## ###############################################################
def findIndexCrossed(lst, value, offset=0):
  return [
    i + offset
    for i in range(len(lst)-1)
    if (lst[i] <= value and lst[i+1] > value) or (lst[i] >= value and lst[i+1] < value)
  ]

def computeDerivative(x, y):
  delta_x = x[1] - x[0] # assumes uniform spacing
  dy_dx = [
    (y[i+1] - y[i-1]) / (2 * delta_x)
    for i in range(1, len(x)-1)
  ]
  return x[1:-1], dy_dx

def getClosestValueThatIsSmaller(list_vals, value):
  list_smaller_values = [
    val
    for val in list_vals
    if val < value
  ]
  return max(list_smaller_values, default=None)

def getClosestValueThatIsLarger(list_vals, value):
  list_larger_values = [
    val
    for val in list_vals
    if val > value
  ]
  return min(list_larger_values, default=None)


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class MeasurePhases():
  def __init__(
      self,
      fig, axs, directory_sim, dict_sim_inputs,
      bool_verbose = True
    ):
    ## save input arguments
    self.fig              = fig
    self.axs              = axs
    self.directory_sim    = directory_sim
    self.dict_sim_inputs  = dict_sim_inputs
    self.bool_verbose     = bool_verbose

  def performRoutines(self):
    if self.bool_verbose: print("Loading volume integrated quantities...")
    self.bool_enough_data = False
    self.bool_SSD_growth  = False
    self.bool_fitted      = False
    self._loadData()
    if not(self.bool_enough_data):
      if self.bool_verbose: print("Not enough data to perform analysis.")
      return
    if self.bool_verbose: print("Plotting volume integrated quantities...")
    self._plotData()
    self._findRegimes()
    self.bool_fitted = True
    self._labelPlots()

  def getFittedParams(self):
    if not self.bool_fitted: return None
    dict_sim_summary = {
      "bool_SSD_growth" : self.bool_SSD_growth
    }
    if self.bool_SSD_growth:
      dict_sim_summary.update({
        "exp_regime" : {
          "growth_rate" : {
            "ave" : self.Eratio_gamma_exp_ave,
            "std" : self.Eratio_gamma_exp_std
          }
        },
        "nl_regime" : {
          "growth_rate" : {
            "ave" : self.Eratio_gamma_nl_ave,
            "std" : self.Eratio_gamma_nl_std
          },
          "forced"     : self.bool_forced,
          "start_time" : self.time_nl_start,
          "end_time"   : self.time_nl_end
        },
        "sat_regime" : {
          "E_ratio" : {
            "ave" : self.Eratio_sat_ave,
            "std" : self.Eratio_sat_std
          }
        }
      })
    return dict_sim_summary

  def saveFittedParams(self, directory_sim):
    dict_sim_summary = self.getFittedParams()
    if dict_sim_summary is None: return
    FlashData.saveSimSummary(directory_sim, dict_sim_summary)

  def _loadData(self):
    ## load magnetic energy
    self.data_time, self.data_Emag = LoadData.loadVIData(
      directory  = self.directory_sim,
      field_name = "mag",
      t_turb     = self.dict_sim_inputs["t_turb"],
      time_start = 2.0,
      time_end   = np.inf
    )
    ## load kinetic energy
    self.data_time, self.data_Ekin = LoadData.loadVIData(
      directory  = self.directory_sim,
      field_name = "kin",
      t_turb     = self.dict_sim_inputs["t_turb"],
      time_start = 2.0,
      time_end   = np.inf
    )
    ## define energy ratio
    self.data_Eratio = [
      Emag / Ekin
      for Ekin, Emag in zip(
        self.data_Ekin,
        self.data_Emag
      )
    ]
    ## define plot domain
    self.bool_enough_data = len(self.data_time) > 10
    if not(self.bool_enough_data): return
    self.max_time = max([ 100, max(self.data_time) ])
    self.bool_SSD_growth   = np.log10(np.max(self.data_Emag)) - np.log10(np.min(self.data_Emag)) > 4.0
    self.bool_forced       = False
    self.time_nl_start     = None
    self.time_nl_end       = None
    ## load linear phase time bounds if it exists
    if WWFnF.checkFileExists(self.directory_sim, FileNames.FILENAME_SIM_SUMMARY):
      dict_sim_outputs = WWObjs.readJsonFile2Dict(self.directory_sim, FileNames.FILENAME_SIM_SUMMARY, bool_verbose=False)
      try:
        self.bool_forced   = dict_sim_outputs["nl_regime"]["forced"]
        self.time_nl_start = dict_sim_outputs["nl_regime"]["start_time"]
        self.time_nl_end   = dict_sim_outputs["nl_regime"]["end_time"]
      except KeyError: pass

  def _plotData(self):
    self.axs[0][0].plot(self.data_time, np.log(self.data_Emag),   color="orange", ls="-", lw=2, zorder=3)
    self.axs[1][0].plot(self.data_time, self.data_Emag,           color="orange", ls="-", lw=2, zorder=3)
    self.axs[0][2].plot(self.data_time, np.log(self.data_Eratio), color="orange", ls="-", lw=2, zorder=3)
    self.axs[1][2].plot(self.data_time, self.data_Eratio,         color="orange", ls="-", lw=2, zorder=3)

  def _findRegimes(self):
    if not(self.bool_SSD_growth): return
    if self.bool_verbose: print("Looking for SSD growth phase...")
    sampled_time             = np.linspace(5, np.max(self.data_time), 100)
    sampled_ln_Emag          = interpolate.CubicSpline(self.data_time, np.log(self.data_Emag))(sampled_time)
    sampled_ln_Emag_smoothed = ndimage.gaussian_filter1d(sampled_ln_Emag, sigma=3)
    dt1, d1_ln_Emag_dt1      = computeDerivative(sampled_time, sampled_ln_Emag_smoothed)
    dt2, d2_ln_Emag_dt2      = computeDerivative(dt1, d1_ln_Emag_dt1)
    self.axs[0][0].plot(sampled_time, sampled_ln_Emag_smoothed,         color="blue", ls="-", lw=2, zorder=5)
    self.axs[1][0].plot(sampled_time, np.exp(sampled_ln_Emag_smoothed), color="blue", ls="-", lw=2, zorder=5)
    self.axs[2][0].plot(dt1, d1_ln_Emag_dt1, ls="-", lw=2, color="blue")
    self.axs[2][0].axhline(0.0, color="red", ls="-", lw=2)
    self.axs[3][0].plot(dt2, d2_ln_Emag_dt2, ls="-", lw=2, color="blue")
    self.axs[3][0].axhline(0.0, color="red", ls="-", lw=2)
    range = 1.05 * np.abs(np.min(d2_ln_Emag_dt2))
    self.axs[3][0].set_ylim([ -range, range ])
    if not(self.bool_forced):
      ## method 1: tolerances on d(ln(E))/d(t)
      if self.bool_verbose: print("Fitting non-linear growth phase...")
      d1_tol_min = 0.02 * max(d1_ln_Emag_dt1)
      d1_tol_max = 0.7  * max(d1_ln_Emag_dt1)
      self.axs[2][0].axhline(d1_tol_min, color="red", ls="--", lw=2, alpha=0.5)
      self.axs[2][0].axhline(d1_tol_max, color="red", ls="--", lw=2, alpha=0.5)
      list_d1_min_crosses = findIndexCrossed(d1_ln_Emag_dt1, d1_tol_min)
      list_d1_max_crosses = findIndexCrossed(d1_ln_Emag_dt1, d1_tol_max)
      self.index_nl_start = list_d1_max_crosses[-1]
      list_index_after_linear = [
        val
        for val in list_d1_min_crosses
        if val > self.index_nl_start
      ]
      if len(list_index_after_linear) > 0: self.index_nl_end = list_index_after_linear[0]
      else: self.index_nl_end = len(sampled_time) - 1
      # ## method 2: also add d^2(ln(E))/d(t)^2 = 0 information
      # self.index_nl_start = findIndexCrossed(d2_ln_Emag_dt2[:self.index_nl_start], 0)[-1] + 1
      # self.index_nl_end   = findIndexCrossed(d2_ln_Emag_dt2[self.index_nl_end:], 0, self.index_nl_end)[0] + 1
      ## get output time
      self.time_nl_start = sampled_time[self.index_nl_start]
      self.time_nl_end   = sampled_time[self.index_nl_end]
    else:
      self.index_nl_start = findIndexCrossed(sampled_time, self.time_nl_start)[0]
      self.index_nl_end   = findIndexCrossed(sampled_time, self.time_nl_end)[0]
    for ax in (np.array(self.axs)).flatten():
      ax.axvline(self.time_nl_start, color="red", ls="-", lw=2)
      ax.axvline(self.time_nl_end, color="red", ls="-", lw=2)
      ax.set_xlim([ 1, 1.05*self.max_time ])
    sampled_ln_Eratio = interpolate.CubicSpline(self.data_time, np.log(self.data_Eratio))(sampled_time)
    self.axs[0][1].plot(dt1, d1_ln_Emag_dt1 * (dt1 - self.time_nl_start), ls="-", lw=2, color="blue")
    self.axs[0][1].set_ylim([0, 4])
    FitFuncs.fitLinearFunc(
      data_x            = sampled_time,
      data_y            = sampled_ln_Emag,
      index_end_fit     = self.index_nl_start,
      ax                = self.axs[0][0],
      num_interp_points = 10**2,
      color             = "green",
      linestyle         = "--"
    )
    Emag_gamma_nl_ave, _ = FitFuncs.fitLinearFunc(
      data_x            = sampled_time,
      data_y            = np.exp(sampled_ln_Emag),
      index_start_fit   = self.index_nl_start,
      index_end_fit     = self.index_nl_end,
      ax                = self.axs[1][0],
      num_interp_points = 10**2,
      color             = "green",
      linestyle         = "--"
    )
    self.Eratio_gamma_exp_ave, self.Eratio_gamma_exp_std = FitFuncs.fitLinearFunc(
      data_x            = sampled_time,
      data_y            = sampled_ln_Eratio,
      index_end_fit     = self.index_nl_start,
      ax                = self.axs[0][2],
      num_interp_points = 10**2,
      color             = "green",
      linestyle         = "--"
    )
    self.Eratio_gamma_nl_ave, self.Eratio_gamma_nl_std = FitFuncs.fitLinearFunc(
      data_x            = sampled_time,
      data_y            = np.exp(sampled_ln_Eratio),
      index_start_fit   = self.index_nl_start,
      index_end_fit     = self.index_nl_end,
      ax                = self.axs[1][2],
      num_interp_points = 10**2,
      color             = "green",
      linestyle         = "--"
    )
    self.axs[2][0].axhline(self.Eratio_gamma_exp_ave, color="green", ls="--", lw=2)
    self.axs[2][1].axhline(0.0, color="red", ls="-", lw=2)
    self.axs[3][1].axhline(0.0, color="red", ls="-", lw=2)
    Emag_sat_ave = np.mean(np.exp(sampled_ln_Emag[self.index_nl_end:]))
    self.axs[0][0].axhline(np.log(Emag_sat_ave), color="green", ls=":", lw=2)
    self.axs[1][0].axhline(Emag_sat_ave, color="green", ls=":", lw=2)
    self.Eratio_sat_ave = np.mean(np.exp(sampled_ln_Eratio[self.index_nl_end:]))
    self.Eratio_sat_std = np.std(np.exp(sampled_ln_Eratio[self.index_nl_end:]))
    self.axs[0][2].axhline(np.log(self.Eratio_sat_ave), color="green", ls=":", lw=2)
    self.axs[1][2].axhline(self.Eratio_sat_ave, color="green", ls=":", lw=2)
    sampled_Emag_smoothed = np.exp(sampled_ln_Emag_smoothed)
    dt1, d1_Emag_dt1 = computeDerivative(sampled_time, sampled_Emag_smoothed)
    dt2, d2_Emag_dt2 = computeDerivative(dt1, d1_Emag_dt1)
    dln_dbdt_dlnt = 1 + (dt2 - self.time_nl_start) / d1_Emag_dt1[1:-1] * d2_Emag_dt2
    self.axs[2][1].axhline(Emag_gamma_nl_ave, color="green", ls="--", lw=2)
    self.axs[2][1].plot(dt1, d1_Emag_dt1,   color="blue", ls="-", lw=2)
    self.axs[3][1].plot(dt2, d2_Emag_dt2,   color="blue", ls="-", lw=2)
    self.axs[1][1].plot(dt2, dln_dbdt_dlnt, color="blue", ls="-", lw=2)
    self.axs[1][1].set_ylim([ -1, 3 ])

  def _labelPlots(self):
    self.axs[-1][0].set_xlabel(r"$t / t_\mathrm{turb}$")
    self.axs[-1][1].set_xlabel(r"$t / t_\mathrm{turb}$")
    self.axs[-1][2].set_xlabel(r"$t / t_\mathrm{turb}$")
    self.axs[0][0].set_ylabel(r"$\ln(E_\mathrm{mag})$")
    self.axs[1][0].set_ylabel(r"$E_\mathrm{mag}$")
    self.axs[2][0].set_ylabel(r"$t {\rm d}\ln(E_\mathrm{mag}) / {\rm d}(t / t_\mathrm{turb})$")
    self.axs[3][0].set_ylabel(r"${\rm d}^2\ln(E_\mathrm{mag}) / {\rm d}(t / t_\mathrm{turb})^2$")
    self.axs[0][1].set_ylabel(r"$(t - t_\mathrm{nl}) \,{\rm d}\ln(E_\mathrm{mag}) / {\rm d}(t / t_\mathrm{turb})$")
    self.axs[1][1].set_ylabel(r"$\mathrm{d}\ln(\mathrm{d}E_\mathrm{mag}/\mathrm{d}t) / \mathrm{d}\ln(t / t_\mathrm{turb}) + 1$")
    self.axs[2][1].set_ylabel(r"${\rm d} E_\mathrm{mag} / {\rm d}(t / t_\mathrm{turb})$")
    self.axs[3][1].set_ylabel(r"${\rm d}^2 E_\mathrm{mag} / {\rm d}(t / t_\mathrm{turb})^2$")
    self.axs[0][2].set_ylabel(r"$\ln(E_\mathrm{mag} / E_\mathrm{kin})$")
    self.axs[1][2].set_ylabel(r"$E_\mathrm{mag} / E_\mathrm{kin}$")
    if self.bool_forced:
      self.axs[1][0].text(
        0.05, 0.935, r"forced range",
        fontsize=22, color="black", ha="left", va="top",
        transform=self.axs[1][0].transAxes
      )
    FlashData.addLabel_simInputs(
      fig             = self.fig,
      ax              = self.axs[0][0],
      dict_sim_inputs = self.dict_sim_inputs,
      bbox            = (1,0),
      vpos            = (0.95, 0.05),
      bool_show_res   = True
    )


## ###############################################################
## OPPERATOR HANDLING PLOT CALLS
## ###############################################################
def plotSimData(
    directory_sim,
    bool_save_data = True,
    bool_verbose   = True,
    lock           = None,
    **kwargs
  ):
  dict_sim_inputs = FlashData.readSimInputs(directory_sim, bool_verbose=False)
  if len(LIST_SIM_NAMES) > 0:
    sim_name = FlashData.getSimName(dict_sim_inputs)
    if not(sim_name in LIST_SIM_NAMES): return
  print("Looking at:", directory_sim)
  directory_vis = f"{directory_sim}/vis_folder/"
  WWFnF.createDirectory(directory_vis, bool_verbose=False)
  ## INITIALISE FIGURE
  ## -----------------
  if bool_verbose: print("Initialising figure...")
  num_rows = 4
  num_cols = 3
  fig, fig_grid = PlotFuncs.createFigure_grid(
    fig_scale        = 1.0,
    fig_aspect_ratio = (5.0, 8.0),
    num_rows         = num_rows,
    num_cols         = num_cols
  )
  ## PLOT INTEGRATED QUANTITIES
  ## --------------------------
  obj_measure_phases = MeasurePhases(
    fig              = fig,
    axs              = [[
        fig.add_subplot(fig_grid[row_index, col_index])
        for col_index in range(num_cols)
      ] for row_index in range(num_rows)
    ],
    directory_sim   = directory_sim,
    dict_sim_inputs = dict_sim_inputs,
    bool_verbose    = bool_verbose
  )
  obj_measure_phases.performRoutines()
  ## SAVE FIGURE + DATASET
  ## ---------------------
  if lock is not None: lock.acquire()
  if bool_save_data: obj_measure_phases.saveFittedParams(directory_sim)
  sim_name = FlashData.getSimName(dict_sim_inputs)
  fig_name = f"{sim_name}_measure_phases.png"
  if bool_verbose: print(f"Saving figure...")
  PlotFuncs.saveFigure(fig, f"{directory_vis}/{fig_name}", bool_verbose=True)
  if lock is not None: lock.release()
  if bool_verbose: print(" ")


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  parser = WWArgparse.MyParser(description="Calculate kinetic and magnetic energy spectra.")
  args_opt = parser.add_argument_group(description="Optional processing arguments:")
  args_opt.add_argument("-sim_path",  default=None, type=str, required=False, help="type: %(type)s")
  args_opt.add_argument("-save_data", default=False, **WWArgparse.OPT_BOOL_ARG)
  args = vars(parser.parse_args())
  directory_sim  = args["sim_path"]
  bool_save_data = args["save_data"]
  if directory_sim is None:
    FlashData.callFuncForAllSimulations(
      func               = functools.partial(plotSimData, bool_save_data=BOOL_SAVE_DATA),
      bool_mproc         = BOOL_MPROC,
      list_base_paths    = LIST_BASE_PATHS,
      list_suite_folders = LIST_SUITE_FOLDERS,
      list_mach_folders  = LIST_MACH_FOLDERS,
      list_sim_folders   = LIST_SIM_FOLDERS,
      list_res_folders   = LIST_RES_FOLDERS
    )
  else:
    if WWFnF.checkDirectoryExists(directory_sim): plotSimData(directory_sim, bool_save_data=bool_save_data)
    else: raise Exception("Directory does not exist.")


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM