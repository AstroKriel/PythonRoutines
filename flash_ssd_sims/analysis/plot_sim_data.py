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

## load user defined routines
from plot_vi_data import PlotTurbData

## load user defined modules
from TheFlashModule import FlashData, FileNames
from TheUsefulModule import WWFnF, WWArgparse, WWLists, WWObjs
from TheFittingModule import FitMHDScales, FitFuncs
from TheAnalysisModule import WWSpectra
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

# ## subset of simulations
# BOOL_MPROC         = 0
# LIST_SUITE_FOLDERS = [ "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm2" ]
# LIST_RES_FOLDERS   = [ "144" ]

# ## full list of simulations
# BOOL_MPROC         = 0
# LIST_SUITE_FOLDERS = [ "Re50", "Re250", "Re500", "Re750", "Rm3000" ]
# LIST_MACH_FOLDERS  = [ "Mach0.2", "Mach5" ]
# LIST_SIM_FOLDERS   = [ "Pm1", "Pm2", "Pm5", "Pm10", "Pm20", "Pm40", "Pm50", "Pm60", "Pm125" ]
# LIST_RES_FOLDERS   = [ "18", "36", "72", "144", "288" ]


## ###############################################################
## HELPER FUNCTIONS
## ###############################################################
def reynoldsSpectrum(list_k_turb, list_power, diss_rate):
  list_power_reverse = np.array(list_power[::-1])
  list_sqt_sum_power = np.sqrt(np.cumsum(list_power_reverse))[::-1]
  return list_sqt_sum_power / (diss_rate * np.array(list_k_turb))

def measureViscousScale(list_k_turb, spectra_group_t):
  scales_group_t = []
  for _, list_power in enumerate(spectra_group_t):
    if np.log10(min(list_power)) < -0.25:
      list_k_interp = np.logspace(np.log10(min(list_k_turb)), np.log10(max(list_k_turb)), 10**4)
      list_power_interp = FitFuncs.interpLogLogData(list_k_turb, list_power, list_k_interp, interp_kind="cubic")
      scale_index = np.argmin(abs(list_power_interp - 1.0))
      scale_k = list_k_interp[scale_index]
    else: scale_k = np.nan
    scales_group_t.append(scale_k)
  return scales_group_t

def dictDeepMerge(dict1, dict2):
  for key, value in dict2.items():
    if isinstance(value, dict) and (key in dict1):
      dictDeepMerge(dict1[key], value)
    else: dict1[key] = value

def getLengthOfList(lst):
  return len([
    val
    for val in lst
    if (val is not np.nan) and (val is not None)
  ])

def removeOutliers(data, threshold=2.0):
  data_array = np.array(data, dtype=np.float64)
  data_array = data_array[~np.isnan(data_array)]
  deviation_from_median = np.abs(data_array - np.nanmedian(data_array))
  median_deviation = np.nanmedian(deviation_from_median)
  modified_z_score = deviation_from_median / median_deviation if median_deviation else np.zeros(len(deviation_from_median))
  data_subset = data_array[modified_z_score < threshold]
  if len(data_subset) < 5: return data_array
  return data_subset


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class PlotSpectra():
  def __init__(
      self,
      fig, ax_spect_ratio, ax_spect_kin, ax_spect_reyh, ax_spect_srt, ax_spect_ch, ax_spect_mag, ax_spect_cur, ax_scales,
      directory_sim, dict_sim_inputs, dict_sim_summary, outputs_per_t_turb,
      bool_verbose = True
    ):
    ## save input arguments
    self.fig                = fig
    self.ax_spect_ratio     = ax_spect_ratio
    self.ax_spect_kin       = ax_spect_kin
    self.ax_spect_reyh      = ax_spect_reyh
    self.ax_spect_srt       = ax_spect_srt
    self.ax_spect_ch        = ax_spect_ch
    self.ax_spect_mag       = ax_spect_mag
    self.ax_spect_cur       = ax_spect_cur
    self.ax_scales          = ax_scales
    self.directory_sim      = directory_sim
    self.dict_sim_inputs    = dict_sim_inputs
    self.dict_sim_summary   = dict_sim_summary
    self.outputs_per_t_turb = outputs_per_t_turb
    self.bool_verbose       = bool_verbose
    self.dict_plot_params_kin = {
      "ax"        : self.ax_spect_kin,
      "cmap_name" : "Blues",
      "color"     : "blue"
    }
    self.dict_plot_params_reyh = {
      "ax"        : self.ax_spect_reyh,
      "cmap_name" : "Purples",
      "color"     : "purple"
    }
    self.dict_plot_params_srt = {
      "ax"        : self.ax_spect_srt,
      "cmap_name" : "Greys",
      "color"     : "black"
    }
    self.dict_plot_params_ch = {
      "ax"        : self.ax_spect_ch,
      "cmap_name" : "Oranges",
      "color"     : "orange"
    }
    self.dict_plot_params_mag = {
      "ax"        : self.ax_spect_mag,
      "cmap_name" : "Reds",
      "color"     : "red"
    }
    self.dict_plot_params_cur = {
      "ax"        : self.ax_spect_cur,
      "cmap_name" : "Greens",
      "color"     : "green"
    }
    self.dict_plot_params_ratio = {
      "ax"        : self.ax_spect_ratio,
      "cmap_name" : "cmr.iceburn",
      "color"     : "black"
    }

  def performRoutines(self):
    self.bool_scales_fitted = False
    if self.bool_verbose: print("Loading growth regime details...")
    self._loadRegimeData()
    if self.bool_verbose: print("Loading spectra data...")
    self._loadSpectra()
    if self.bool_verbose: print("Plotting spectra...")
    self._plotSpectra()
    self._plotSpectraRatio()
    if self.bool_verbose: print("Fitting scales...")
    self._plotMHDScales()
    if self.bool_phases_fitted:
      if self.bool_verbose: print("Measuring scales in SSD phases...")
      self._plotGrowthRegimes()

  def saveFittedParams(self):
    if not(self.bool_phases_fitted) or not(self.bool_scales_fitted): return
    dictDeepMerge(self.dict_sim_summary, self.dict_k_nu_reyh)
    if self.bool_srt_computed: dictDeepMerge(self.dict_sim_summary, self.dict_k_nu_srt)
    dictDeepMerge(self.dict_sim_summary, self.dict_k_tm)
    dictDeepMerge(self.dict_sim_summary, self.dict_k_int)
    dictDeepMerge(self.dict_sim_summary, self.dict_reyh_eff)
    if self.bool_ch_computed: dictDeepMerge(self.dict_sim_summary, self.dict_k_ch)
    dictDeepMerge(self.dict_sim_summary, self.dict_k_p)
    dictDeepMerge(self.dict_sim_summary, self.dict_k_eta)
    dictDeepMerge(self.dict_sim_summary, self.dict_k_p)
    dictDeepMerge(self.dict_sim_summary, self.dict_k_eta)
    FlashData.saveSimSummary(self.directory_sim, self.dict_sim_summary)

  def _loadRegimeData(self):
    self.bool_phases_fitted = False
    if self.dict_sim_summary is None: return
    try:
      self.bool_phases_fitted = self.dict_sim_summary["bool_SSD_growth"]
    except KeyError: return
    try:
      self.bool_forced       = self.dict_sim_summary["nl_regime"]["forced"]
      self.time_linear_start = self.dict_sim_summary["nl_regime"]["start_time"]
      self.time_linear_end   = self.dict_sim_summary["nl_regime"]["end_time"]
    except KeyError: pass

  def _loadSpectra(self):
    ds = FlashData.readSimOutputs(self.directory_sim)
    self.list_k_turb            = list(ds["array_k_turb"].values)
    self.list_t_turb            = list(ds["array_t_turb"].values)
    self.list_power_kin_group_t = list(ds["kinetic_energy_spectra"].values)
    self.list_power_mag_group_t = list(ds["magnetic_energy_spectra"].values)
    self.list_power_cur_group_t = list(ds["current_density_spectra"].values)
    try:
      self.list_power_srt_group_t = list(ds["strain_rate_tensor_spectra"].values)
      self.bool_srt_computed = True
    except: self.bool_srt_computed = False
    try:
      self.list_power_ch_group_t = list(ds["cross_helicity_spectra"].values)
      self.bool_ch_computed = True
    except: self.bool_ch_computed = False
    self.list_power_reyh_group_t = [
      reynoldsSpectrum(self.list_k_turb, list_power, self.dict_sim_inputs["nu"])
      for list_power in self.list_power_kin_group_t
    ]
    self.list_power_ratio_group_t = [
      list_power_mag / list_power_kin
      for list_power_kin, list_power_mag in zip(
        self.list_power_kin_group_t,
        self.list_power_mag_group_t
      )
    ]

  def _plotSpectraRatio(self):
    log10_power_ratio_group_t = np.log10(self.list_power_ratio_group_t)
    cmap, norm = PlotFuncs.createCmap(
      self.dict_plot_params_ratio["cmap_name"],
      vmin = 0.9*np.min(log10_power_ratio_group_t),
      vmid = 0,
      vmax = 1.1*np.max(log10_power_ratio_group_t)
    )
    self.dict_plot_params_ratio["ax"].imshow(
      log10_power_ratio_group_t.T,
      cmap=cmap, norm=norm, aspect="auto", origin="lower",
      extent=[
        min(self.list_t_turb), max(self.list_t_turb),
        min(self.list_k_turb), max(self.list_k_turb)
      ]
    )
    self.dict_plot_params_ratio["ax"].set_ylabel(r"$k / k_\mathrm{turb}$")
    self.dict_plot_params_ratio["ax"].set_yscale("log")
    PlotFuncs.addColorbar_fromCmap(
      fig        = self.fig,
      ax         = self.dict_plot_params_ratio["ax"],
      cmap       = cmap,
      norm       = norm,
      cbar_title = r"$\log_{10}\big(E_\mathrm{mag}(k) / E_\mathrm{kin}(k)\big)$",
      fontsize   = 20
    )

  def _plotSpectra(self):
    def __adjustAxis(ax, str_label):
      ax.set_xlim([ 0.9, 1.1*max(self.list_k_turb) ])
      ax.set_xscale("log")
      ax.set_yscale("log")
      ax.set_ylabel(str_label)
    def __plotSpectra(dict_plot_params, spectra_group_t, bool_norm=False):
      cmap, norm = PlotFuncs.createCmap(
        dict_plot_params["cmap_name"],
        vmin = 0,
        vmax = len(spectra_group_t),
        cmin = 0.25
      )
      for index, list_power in enumerate(spectra_group_t):
        if bool_norm: list_power = WWSpectra.normSpectra(list_power)
        dict_plot_params["ax"].plot(
          self.list_k_turb,
          list_power,
          color=cmap(norm(index)),
          ls="-", lw=1.0, alpha=0.5, zorder=5
        )
    ## plot spectra
    __plotSpectra(self.dict_plot_params_kin,  self.list_power_kin_group_t)
    __plotSpectra(self.dict_plot_params_reyh, self.list_power_reyh_group_t)
    if self.bool_srt_computed: __plotSpectra(self.dict_plot_params_srt, self.list_power_srt_group_t, bool_norm=True)
    if self.bool_ch_computed:  __plotSpectra(self.dict_plot_params_ch,  self.list_power_ch_group_t,  bool_norm=True)
    __plotSpectra(self.dict_plot_params_mag, self.list_power_mag_group_t, bool_norm=True)
    __plotSpectra(self.dict_plot_params_cur, self.list_power_cur_group_t, bool_norm=True)
    ## tweak axis
    __adjustAxis(self.ax_spect_kin,  r"$E_\mathrm{kin}(k)$")
    __adjustAxis(self.ax_spect_reyh, r"$\mathrm{Re}(k)$")
    __adjustAxis(self.ax_spect_srt,  r"$\widehat{\mathcal{P}}_\mathrm{SRT}(k)$")
    __adjustAxis(self.ax_spect_ch,   r"$\widehat{\mathcal{P}}_\mathrm{CH}(k)$")
    __adjustAxis(self.ax_spect_mag,  r"$\widehat{E}_\mathrm{mag}(k)$")
    __adjustAxis(self.ax_spect_cur,  r"$\widehat{E}_\mathrm{cur}(k)$")
    self.ax_spect_reyh.axhline(y=1.0, ls="--", color="black", lw=1.0, zorder=1)
    self.ax_spect_cur.set_xlabel(r"$k / k_\mathrm{turb}$")

  def _plotMHDScales(self):
    self.k_nu_reyh_group_t = measureViscousScale(self.list_k_turb, self.list_power_reyh_group_t)
    if self.bool_srt_computed:
      self.k_nu_srt_group_t = [
        FitMHDScales.getSpectrumPeakScale(self.list_k_turb, WWSpectra.normSpectra(power_spectrum))[0]
        for power_spectrum in self.list_power_srt_group_t
      ]
    self.k_tm_group_t = [
      np.sqrt(np.sum(power_spectrum) / np.sum(np.array(self.list_k_turb)**2 * np.array(power_spectrum)))
      for power_spectrum in self.list_power_kin_group_t
    ]
    self.k_int_group_t = [
      np.sum(np.array(power_spectrum) / np.array(self.list_k_turb)) / np.sum(power_spectrum)
      for power_spectrum in self.list_power_kin_group_t
    ]
    self.reyh_eff_group_t = [
      (k_int / k_tm)**2
      for k_tm, k_int in zip(self.k_tm_group_t, self.k_int_group_t)
    ]
    if self.bool_ch_computed:
      self.k_ch_group_t = [
        FitMHDScales.getSpectrumPeakScale(self.list_k_turb, WWSpectra.normSpectra(power_spectrum))[0]
        for power_spectrum in self.list_power_ch_group_t
      ]
    self.k_eta_group_t = [
      FitMHDScales.getSpectrumPeakScale(self.list_k_turb, WWSpectra.normSpectra(power_spectrum))[0]
      for power_spectrum in self.list_power_cur_group_t
    ]
    self.k_p_group_t = [
      FitMHDScales.getSpectrumPeakScale(self.list_k_turb, WWSpectra.normSpectra(power_spectrum))[0]
      for power_spectrum in self.list_power_mag_group_t
    ]
    dict_plot_args = { "ls":"-", "zorder":3, "lw":1.5 }
    self.ax_scales.plot(
      self.list_t_turb,
      self.k_nu_reyh_group_t,
      color = self.dict_plot_params_reyh["color"],
      **dict_plot_args
    )
    if self.bool_srt_computed: 
      self.ax_scales.plot(
        self.list_t_turb,
        self.k_nu_srt_group_t,
        color = self.dict_plot_params_srt["color"],
        **dict_plot_args
      )
    if self.bool_ch_computed:
      self.ax_scales.plot(
        self.list_t_turb,
        self.k_ch_group_t,
        color = self.dict_plot_params_ch["color"],
        **dict_plot_args
      )
    self.ax_scales.plot(
      self.list_t_turb,
      self.k_p_group_t,
      color = self.dict_plot_params_mag["color"],
      **dict_plot_args
    )
    self.ax_scales.plot(
      self.list_t_turb,
      self.k_eta_group_t,
      color = self.dict_plot_params_cur["color"],
      **dict_plot_args
    )
    self.ax_scales.set_yscale("log")
    self.ax_scales.set_ylabel(r"$k / k_\mathrm{turb}$")

  def _plotGrowthRegimes(self):
    def __plotScalesInRegimes(label, list_scales, ax_spectra=None, color=None):
      data_exp_regime = removeOutliers(list_scales[index_exp_start:index_linear_start])
      data_sat_regime = removeOutliers(list_scales[index_linear_end:])
      bool_enough_exp_data = len(data_exp_regime) > 5
      bool_enough_sat_data = len(data_sat_regime) > 5
      dict_scale = {
        "exp_regime": {
          label : {
            "ave" : np.nanmedian(data_exp_regime) if bool_enough_exp_data else None,
            "std" : np.nanstd(data_exp_regime)    if bool_enough_exp_data else None,
          }
        },
        "sat_regime": {
          label : {
            "ave" : np.nanmedian(data_sat_regime) if bool_enough_sat_data else None,
            "std" : np.nanstd(data_sat_regime)    if bool_enough_sat_data else None,
          }
        }
      }
      if not (bool_enough_exp_data and bool_enough_sat_data): return dict_scale
      if ax_spectra is None: return dict_scale
      ax_spectra.axvline(x=dict_scale["exp_regime"][label]["ave"], ls="--", lw=2.0, alpha=0.5, color=color, zorder=2)
      ax_spectra.axvspan(
        dict_scale["exp_regime"][label]["ave"] - dict_scale["exp_regime"][label]["std"],
        dict_scale["exp_regime"][label]["ave"] + dict_scale["exp_regime"][label]["std"],
        color=color, alpha=0.25, zorder=1
      )
      ax_spectra.axvline(x=dict_scale["sat_regime"][label]["ave"], ls=":", lw=2.0, alpha=0.5, color=color, zorder=2)
      ax_spectra.axvspan(
        dict_scale["sat_regime"][label]["ave"] - dict_scale["sat_regime"][label]["std"],
        dict_scale["sat_regime"][label]["ave"] + dict_scale["sat_regime"][label]["std"],
        color=color, alpha=0.25, zorder=1
      )
      self.ax_scales.axhline(y=dict_scale["exp_regime"][label]["ave"], ls="--", lw=1.0, color=color, zorder=1)
      self.ax_scales.axhspan(
        dict_scale["exp_regime"][label]["ave"] - dict_scale["exp_regime"][label]["std"],
        dict_scale["exp_regime"][label]["ave"] + dict_scale["exp_regime"][label]["std"],
        color=color, alpha=0.25, zorder=1
      )
      self.ax_scales.axhline(y=dict_scale["sat_regime"][label]["ave"], ls=":", lw=1.0, color=color, zorder=1)
      self.ax_scales.axhspan(
        dict_scale["sat_regime"][label]["ave"] - dict_scale["sat_regime"][label]["std"],
        dict_scale["sat_regime"][label]["ave"] + dict_scale["sat_regime"][label]["std"],
        color=color, alpha=0.25, zorder=1
      )
      return dict_scale
    ## get indices of key time points
    index_exp_start    = WWLists.getIndexClosestValue(self.list_t_turb, 5)
    index_linear_start = WWLists.getIndexClosestValue(self.list_t_turb, self.time_linear_start)
    index_linear_end   = WWLists.getIndexClosestValue(self.list_t_turb, self.time_linear_end)
    ## indicate nonlinear growth stage
    self.ax_scales.axvline(x=self.time_linear_start, ls="--", color="black", lw=1.0, zorder=1)
    self.ax_scales.axvline(x=self.time_linear_end,   ls="--", color="black", lw=1.0, zorder=1)
    self.ax_scales.axvspan(self.time_linear_start, self.time_linear_end, color="grey", alpha=0.5, zorder=2 )
    ## plot average scale in kinematic and saturated stages
    self.dict_k_nu_reyh = __plotScalesInRegimes("k_nu_reyh", self.k_nu_reyh_group_t, self.dict_plot_params_reyh["ax"], self.dict_plot_params_reyh["color"])
    if self.bool_srt_computed: self.dict_k_nu_srt = __plotScalesInRegimes("k_nu_srt", self.k_nu_srt_group_t, self.dict_plot_params_srt["ax"], self.dict_plot_params_srt["color"])
    if self.bool_ch_computed:  self.dict_k_ch     = __plotScalesInRegimes("k_ch",     self.k_ch_group_t,     self.dict_plot_params_ch["ax"],  self.dict_plot_params_ch["color"])
    self.dict_k_tm       = __plotScalesInRegimes("k_tm",     self.k_tm_group_t)
    self.dict_k_int      = __plotScalesInRegimes("k_int",    self.k_int_group_t)
    self.dict_reyh_eff   = __plotScalesInRegimes("reyh_eff", self.reyh_eff_group_t)
    self.dict_k_p        = __plotScalesInRegimes("k_p",      self.k_p_group_t,   self.dict_plot_params_mag["ax"], self.dict_plot_params_mag["color"])
    self.dict_k_eta      = __plotScalesInRegimes("k_eta",    self.k_eta_group_t, self.dict_plot_params_cur["ax"], self.dict_plot_params_cur["color"])
    self.bool_scales_fitted = True


## ###############################################################
## OPPERATOR HANDLING PLOT CALLS
## ###############################################################
def plotSimData(
    directory_sim, bool_save_data,
    lock         = None,
    bool_verbose = True,
    **kwargs
  ):
  print(f"Looking at: {directory_sim}")
  dict_sim_inputs = FlashData.readSimInputs(directory_sim)
  if WWFnF.checkFileExists(directory_sim, FileNames.FILENAME_SIM_SUMMARY):
    dict_sim_summary = FlashData.readSimSummary(directory_sim)
  else: dict_sim_summary = None
  directory_vis = f"{directory_sim}/vis_folder/"
  WWFnF.createDirectory(directory_vis, bool_verbose=False)
  ## INITIALISE FIGURE
  ## -----------------
  if bool_verbose: print("Initialising figure...")
  fig, fig_grid = PlotFuncs.createFigure_grid(
    fig_scale        = 0.6,
    fig_aspect_ratio = (6.0, 10.0), # height, width
    num_rows         = 6,
    num_cols         = 2
  )
  ax_spect_ratio = fig.add_subplot(fig_grid[0, 0])
  ax_scales      = fig.add_subplot(fig_grid[1:3, 0])
  ax_Mach        = fig.add_subplot(fig_grid[3, 0])
  ax_vi_Eratio   = fig.add_subplot(fig_grid[4:, 0])
  # ax_dt_Emag     = fig.add_subplot(fig_grid[4, 0])
  ax_spect_kin   = fig.add_subplot(fig_grid[0, 1])
  ax_spect_reyh  = fig.add_subplot(fig_grid[1, 1])
  ax_spect_srt   = fig.add_subplot(fig_grid[2, 1])
  ax_spect_ch    = fig.add_subplot(fig_grid[3, 1])
  ax_spect_mag   = fig.add_subplot(fig_grid[4, 1])
  ax_spect_cur   = fig.add_subplot(fig_grid[5, 1])
  ## PLOT VOLUME INTEGRATED QUANTITIES
  ## ---------------------------------
  obj_plot_turb = PlotTurbData(
    fig              = fig,
    axs              = [ ax_Mach, ax_vi_Eratio ],
    directory_sim    = directory_sim,
    dict_sim_inputs  = dict_sim_inputs,
    dict_sim_summary = dict_sim_summary,
    bool_verbose     = bool_verbose
  )
  obj_plot_turb.performRoutines()
  ## PLOT SPECTRA + DERIVED SCALES
  ## -----------------------------
  obj_plot_spectra = PlotSpectra(
    fig                = fig,
    ax_spect_ratio     = ax_spect_ratio,
    ax_spect_kin       = ax_spect_kin,
    ax_spect_reyh      = ax_spect_reyh,
    ax_spect_srt       = ax_spect_srt,
    ax_spect_ch        = ax_spect_ch,
    ax_spect_mag       = ax_spect_mag,
    ax_spect_cur       = ax_spect_cur,
    ax_scales          = ax_scales,
    directory_sim      = directory_sim,
    dict_sim_inputs    = dict_sim_inputs,
    dict_sim_summary   = dict_sim_summary,
    outputs_per_t_turb = obj_plot_turb.outputs_per_t_turb,
    bool_verbose       = bool_verbose
  )
  obj_plot_spectra.performRoutines()
  ## SAVE FIGURE + DATASET
  ## ---------------------
  if lock is not None: lock.acquire()
  if bool_save_data: obj_plot_spectra.saveFittedParams()
  sim_name = FlashData.getSimName(dict_sim_inputs)
  fig_name = f"{sim_name}_dataset.png"
  PlotFuncs.saveFigure(fig, f"{directory_vis}/{fig_name}", bool_verbose=True)
  if lock is not None: lock.release()
  if bool_verbose: print(" ")


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  parser = WWArgparse.MyParser(description="Plot and derive all relevant SSD data.")
  args_opt = parser.add_argument_group(description="Optional processing arguments:")
  args_opt.add_argument("-sim_path", type=str, required=False, default=None, help="type: %(type)s")
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