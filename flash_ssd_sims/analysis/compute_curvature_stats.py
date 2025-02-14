## ###############################################################
## MODULES
## ###############################################################
import sys, time
import numpy as np
import matplotlib.pyplot as plt

from scipy import stats
from filelock import FileLock

## load user defined modules
from TheFlashModule import LoadData, FileNames
from TheUsefulModule import WWArgparse, WWFnF, WWLists, WWTerminal, WWObjs
from TheFittingModule import FitFuncs
from TheAnalysisModule import WWFields, StatsStuff
from ThePlottingModule import PlotFuncs


## ###############################################################
## PREPARE WORKSPACE
## ###############################################################
plt.switch_backend("agg") # use a non-interactive plotting backend


## ###############################################################
## GLOBAL CONSTANTS
## ###############################################################
BOOL_DEBUG    = 1
EPSILON       = 1e-9
CONTOUR_LEVEL = -2


## ###############################################################
## HELPER FUNCTION
## ###############################################################
def convertFloat2String(val, str_neg=r"$-$", str_pos=r"$+$"):
  str_sgn = str_neg if (val < 0) else str_pos
  return str_sgn + f"{np.abs(val):.2f}"

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

def getFirstIndexCrossingTargetValue(list_vals, target_val):
  list_index_crossed_target = [
    idx
    for idx in range(len(list_vals)-1)
    if (list_vals[idx] <= target_val) and (list_vals[idx+1] >= target_val)
  ]
  return list_index_crossed_target[0] if len(list_index_crossed_target) > 0 else None

def setAxisLimits(ax, bedges, log10_pdf):
  pdf_lower_bound = np.min(log10_pdf) + 0.1 * (np.max(log10_pdf) - np.min(log10_pdf))
  index_min_value = getFirstIndexCrossingTargetValue(log10_pdf,       pdf_lower_bound)
  index_max_value = getFirstIndexCrossingTargetValue(log10_pdf[::-1], pdf_lower_bound)
  bin_lower = bedges[index_min_value]
  bin_upper = bedges[len(bedges)-index_max_value]
  ax.set_xlim(bin_lower, bin_upper)
  return bin_lower, bin_upper


## ###############################################################
## OPERATOR CLASS
## ###############################################################
class ComputeCurvatureStats():
  def __init__(self):
    self.fig, fig_grid = PlotFuncs.createFigure_grid(
      fig_scale        = 0.5,
      fig_aspect_ratio = (6.0, 10.0),
      num_rows         = 3,
      num_cols         = 2
    )
    self.ax_jpdf_kappa_bnorm = self.fig.add_subplot(fig_grid[0:2,:])
    self.ax_pdf_kappa = self.fig.add_subplot(fig_grid[2,0])
    self.ax_pdf_bnorm = self.fig.add_subplot(fig_grid[2,1])
    self._getInputArgs()

  def _getInputArgs(self):
    parser = WWArgparse.MyParser(description="Calculate kinetic and magnetic energy spectra.")
    ## ------------------- DEFINE OPTIONAL ARGUMENTS
    args_opt = parser.add_argument_group(description="Optional processing arguments:")
    args_opt.add_argument("-force_process",  **WWArgparse.OPT_BOOL_ARG, default=False)
    args_opt.add_argument("-update_summary", **WWArgparse.OPT_BOOL_ARG, default=False)
    args_opt.add_argument("-index_start",    **WWArgparse.OPT_ARG, type=int, default=0)
    args_opt.add_argument("-index_end",      **WWArgparse.OPT_ARG, type=int, default=5000)
    args_opt.add_argument("-num_files",      **WWArgparse.OPT_ARG, type=int, default=100)
    ## ------------------- DEFINE REQUIRED ARGUMENTS
    args_req = parser.add_argument_group(description="Required processing arguments:")
    args_req.add_argument("-sim_name",          type=str, required=True, help="type: %(type)s")
    args_req.add_argument("-sim_regime",       type=str, required=True, help="type: %(type)s")
    args_req.add_argument("-directory_inputs",  type=str, required=True, help="type: %(type)s")
    args_req.add_argument("-directory_outputs", type=str, required=True, help="type: %(type)s")
    args_req.add_argument("-num_cells",         type=int, required=True, help="type: %(type)s")
    args_req.add_argument("-num_blocks",        type=int, required=True, help="type: %(type)s (x3)", nargs=3)
    ## open arguments
    args = vars(parser.parse_args())
    ## save parameters
    self.bool_force_process  = args["force_process"]
    self.bool_update_summary = args["update_summary"]
    self.sim_name            = args["sim_name"]
    self.sim_regime          = args["sim_regime"]
    self.directory_inputs    = args["directory_inputs"]
    self.directory_outputs   = args["directory_outputs"]
    self.directory_vis       = f"{self.directory_outputs}/vis_folder/"
    lock = FileLock("vis.folder.lock")
    with lock: WWFnF.createDirectory(self.directory_vis, bool_verbose=False)
    self.file_index_start    = int(args["index_start"])
    self.file_index_end      = int(args["index_end"])
    self.num_files           = int(args["num_files"])
    self.num_cells           = int(args["num_cells"])
    self.num_blocks          = [
      int(blocks_per_dim)
      for blocks_per_dim in args["num_blocks"]
    ]
    ## simulation domain information
    self.num_procs  = [
      int(self.num_cells / blocks_per_dim)
      for blocks_per_dim in self.num_blocks
    ]
    ## report input parameters
    WWTerminal.printLine(" ")
    WWTerminal.printLine([f"Looking at {self.sim_name} in {self.sim_regime}"])
    if self.bool_force_process: WWTerminal.printLine("Forced: Processing all data.")
    WWTerminal.printLine(["Simulation data stored in:",      self.directory_inputs])
    WWTerminal.printLine(["Saving data summary to:",         self.directory_outputs])
    WWTerminal.printLine(["Number of domain cells:",         str(self.num_cells)])
    WWTerminal.printLine(["Number of blocks per dimension:", str(self.num_blocks)])
    WWTerminal.printLine([f"Processing {self.num_files:d} files betwen indices [{self.file_index_start:d}, {self.file_index_end:d}]"])
    WWTerminal.printLine(" ")

  def performRoutine(self):
    self._getSimFilenames()
    bool_summary_data_exists = WWFnF.checkFileExists(self.directory_outputs, FileNames.FILENAME_SIM_SUMMARY)
    if not(self.bool_force_process) and bool_summary_data_exists:
      self._readCurvatureData()
    elif len(self.list_filenames) > 0:
      self.bool_update_summary = True
      self._computeCurvatureData()
    else: raise Exception(f"Error: No data exists")
    self._plot2DPDF()
    self._plot1DPDFs()
    self._addAnotations()
    PlotFuncs.saveFigure(self.fig, f"{self.directory_vis}/{self.sim_name}_curvature.png")
    if self.bool_update_summary: self._saveDataSummary()

  def _getSimFilenames(self):
    self.list_filenames = WWFnF.getFilesInDirectory(
      directory             = self.directory_inputs, 
      filename_starts_with  = "Turb_hdf5_plt_cnt",
      filename_not_contains = "spect",
      loc_file_index        = 4,
      file_start_index      = self.file_index_start,
      file_end_index        = self.file_index_end,
      num_words             = 5,
    )
    self.list_filenames = WWLists.subsetList(self.list_filenames, self.num_files)

  def _readCurvatureData(self):
    if BOOL_DEBUG:
      dict_curvature = self.__computeCurvature(self.list_filenames[0])
      self.log10_kappa = dict_curvature["log10_kappa"]
      self.log10_bnorm = dict_curvature["log10_bnorm"]
    try:
      lock = FileLock("summary.json.lock")
      with lock:
        dict_data_summary = WWObjs.readJsonFile2Dict(self.directory_outputs, FileNames.FILENAME_SIM_SUMMARY)[self.sim_regime]["curvature"]
        self.bedges_log10_kappa     = np.array(dict_data_summary["bedges_log10_kappa"])
        self.bedges_log10_bnorm     = np.array(dict_data_summary["bedges_log10_bnorm"])
        self.dict_log10_kappa_bnorm = dict_data_summary["dict_log10_kappa_bnorm"]
        self.dict_log10_kappa       = dict_data_summary["dict_log10_kappa"]
        self.dict_log10_bnorm       = dict_data_summary["dict_log10_bnorm"]
    except KeyError as key:
      WWTerminal.printLine(f"KeyError: the {key} is not found in the dictionary.")
      self.bool_update_summary = True
      if len(self.list_filenames) > 0: self._computeCurvatureData()
      else: raise Exception(f"Error: No data exists")

  def _saveDataSummary(self):
    lock = FileLock("summary.json.lock")
    with lock:
      WWObjs.saveDict2JsonFile(
        f"{self.directory_outputs}/{FileNames.FILENAME_SIM_SUMMARY}",
        {
          self.sim_regime : {
            "curvature" : {
              "bedges_log10_kappa"     : self.bedges_log10_kappa,
              "bedges_log10_bnorm"     : self.bedges_log10_bnorm,
              "dict_log10_kappa_bnorm" : self.dict_log10_kappa_bnorm,
              "dict_log10_kappa"       : self.dict_log10_kappa,
              "dict_log10_bnorm"       : self.dict_log10_bnorm,
            }
          }
        }
      )

  def __computeCurvature(self, filename):
    WWTerminal.printLine(["\t> Loading:", filename])
    b_field = LoadData.loadFlashDataCube(
      filepath_file = f"{self.directory_inputs}/{filename}",
      num_blocks    = self.num_blocks,
      num_procs     = self.num_procs,
      field_name    = "mag"
    )
    WWTerminal.printLine("\t> Computing quantities...")
    b_magn = WWFields.vfieldMagnitude(b_field)
    b_rms  = WWFields.sfieldRMS(b_magn)
    t_basis, n_basis, b_basis, kappa = WWFields.vfieldTNB(b_field)
    log10_kappa = np.log10(kappa.flatten())
    log10_bnorm = np.log10(b_magn.flatten() / b_rms)
    return {
      "t_basis"     : t_basis,
      "n_basis"     : n_basis,
      "b_basis"     : b_basis,
      "log10_kappa" : log10_kappa,
      "log10_bnorm" : log10_bnorm
    }

  def _computeCurvatureData(self):
    self.bedges_log10_kappa = None
    self.bedges_log10_bnorm = None
    list_jpdfs_log10_kappa_bnorm         = []
    list_slopes_masked_log10_kappa_bnorm = []
    list_pearsonr_log10_kappa_bnorm      = []
    list_pdfs_log10_kappa                = []
    list_pdfs_log10_bnorm                = []
    WWTerminal.printLine(["There are a total of", len(self.list_filenames), "files."])
    WWTerminal.printLine("Loading data...")
    for filename in self.list_filenames:
      ## compute PDFs of quantities at each time realisation
      dict_curvature = self.__computeCurvature(filename)
      log10_kappa = dict_curvature["log10_kappa"]
      log10_bnorm = dict_curvature["log10_bnorm"]
      del dict_curvature
      if self.bedges_log10_kappa is None: self.bedges_log10_kappa = StatsStuff.compute1DBins(log10_kappa, num_bins=100)
      if self.bedges_log10_bnorm is None: self.bedges_log10_bnorm = StatsStuff.compute1DBins(log10_bnorm, num_bins=100)
      _, pdf_log10_kappa = StatsStuff.compute1DPDF(log10_kappa, bin_edges=self.bedges_log10_kappa)
      _, pdf_log10_bnorm = StatsStuff.compute1DPDF(log10_bnorm, bin_edges=self.bedges_log10_bnorm)
      jpdf_log10_kappa_bnorm = StatsStuff.computeJPDF(log10_kappa, log10_bnorm, self.bedges_log10_kappa, self.bedges_log10_bnorm)
      ## perturb PDFs to avoid log10(0)
      jpdf_log10_kappa_bnorm += EPSILON
      pdf_log10_kappa += EPSILON
      pdf_log10_bnorm += EPSILON
      ## measure correlations in joint PDF
      pearsonr = stats.pearsonr(log10_kappa, log10_bnorm)
      _, slope_masked = FitFuncs.fitLineToMasked2DJPDF(
        bedges_cols = self.bedges_log10_kappa,
        bedges_rows = self.bedges_log10_kappa,
        jpdf        = np.log10(jpdf_log10_kappa_bnorm),
        level       = CONTOUR_LEVEL
      )
      ## store measured data
      list_jpdfs_log10_kappa_bnorm.append(np.log10(jpdf_log10_kappa_bnorm))
      list_slopes_masked_log10_kappa_bnorm.append(slope_masked)
      list_pearsonr_log10_kappa_bnorm.append(pearsonr)
      list_pdfs_log10_kappa.append(np.log10(pdf_log10_kappa))
      list_pdfs_log10_bnorm.append(np.log10(pdf_log10_bnorm))
    WWTerminal.printLine(" ")
    ## store last data from the last time step
    self.log10_kappa = log10_kappa
    self.log10_bnorm = log10_bnorm
    ## store summary statistics across time
    self.dict_log10_kappa_bnorm = {
      "jpdf" : {
        "16p" : np.percentile(list_jpdfs_log10_kappa_bnorm, 16, axis=0),
        "50p" : np.percentile(list_jpdfs_log10_kappa_bnorm, 50, axis=0),
        "84p" : np.percentile(list_jpdfs_log10_kappa_bnorm, 84, axis=0)
      },
      "masked-slope" : {
        "16p" : np.percentile(list_slopes_masked_log10_kappa_bnorm, 16),
        "50p" : np.percentile(list_slopes_masked_log10_kappa_bnorm, 50),
        "84p" : np.percentile(list_slopes_masked_log10_kappa_bnorm, 84)
      },
      "pearsonr" : {
        "16p" : np.percentile(list_pearsonr_log10_kappa_bnorm, 16),
        "50p" : np.percentile(list_pearsonr_log10_kappa_bnorm, 50),
        "84p" : np.percentile(list_pearsonr_log10_kappa_bnorm, 84)
      }
    }
    self.dict_log10_kappa = {
      "pdf" : {
        "16p" : np.percentile(list_pdfs_log10_kappa, 16, axis=0),
        "50p" : np.percentile(list_pdfs_log10_kappa, 50, axis=0),
        "84p" : np.percentile(list_pdfs_log10_kappa, 84, axis=0)
      },
      "value" : {
        "16p" : np.percentile(self.log10_kappa, 16),
        "50p" : np.percentile(self.log10_kappa, 50),
        "84p" : np.percentile(self.log10_kappa, 84)
      }
    }
    self.dict_log10_bnorm = {
      "pdf" : {
        "16p" : np.percentile(list_pdfs_log10_bnorm, 16, axis=0),
        "50p" : np.percentile(list_pdfs_log10_bnorm, 50, axis=0),
        "84p" : np.percentile(list_pdfs_log10_bnorm, 84, axis=0)
      },
      "value" : {
        "16p" : np.percentile(self.log10_bnorm, 16),
        "50p" : np.percentile(self.log10_bnorm, 50),
        "84p" : np.percentile(self.log10_bnorm, 84)
      }
    }

  def _plot2DPDF(self):
    ## check the discretised 2D distribution against the raw data
    WWTerminal.printLine("Plotting 2D PDF...")
    mg_rows, mg_cols = np.meshgrid(self.bedges_log10_kappa, self.bedges_log10_bnorm, indexing="ij")
    self.cmap, self.norm = PlotFuncs.createCmap("cmr.voltage_r", vmin=-4.05, vmax=0.05, cmax=0.9)
    self.ax_jpdf_kappa_bnorm.pcolormesh(
      mg_rows,
      mg_cols,
      self.dict_log10_kappa_bnorm["jpdf"]["50p"],
      cmap = self.cmap,
      norm = self.norm
    )
    self.ax_jpdf_kappa_bnorm.errorbar(
      self.dict_log10_kappa["value"]["50p"],
      self.dict_log10_bnorm["value"]["50p"],
      xerr = np.vstack([
        self.dict_log10_kappa["value"]["50p"] - self.dict_log10_kappa["value"]["16p"],
        self.dict_log10_kappa["value"]["84p"] - self.dict_log10_kappa["value"]["50p"]
      ]),
      yerr = np.vstack([
        self.dict_log10_bnorm["value"]["50p"] - self.dict_log10_bnorm["value"]["16p"],
        self.dict_log10_bnorm["value"]["84p"] - self.dict_log10_bnorm["value"]["50p"]
      ]),
      color="red", fmt="o", capsize=7.5, markersize=7, markeredgecolor="black", elinewidth=1.5, linestyle="", zorder=10
    )
    self.ax_jpdf_kappa_bnorm.contour(
      mg_rows[1:, 1:],
      mg_cols[1:, 1:],
      self.dict_log10_kappa_bnorm["jpdf"]["50p"],
      levels=[CONTOUR_LEVEL], linestyles="--", linewidths=1.5, colors="red", zorder=1
    )
    if BOOL_DEBUG:
      self.ax_jpdf_kappa_bnorm.plot(
        self.log10_kappa,
        self.log10_bnorm,
        color="black", ls="", marker=".", markersize=0.05, alpha=0.05, zorder=5
      )

  def _plot1DPDFs(self):
    WWTerminal.printLine("Plotting 1D PDFs...")
    ## check the marginalised distributions against the raw data
    self.ax_pdf_kappa.plot(
      self.bedges_log10_kappa,
      self.dict_log10_kappa["pdf"]["50p"],
      color="blue", ls="-", marker="o", ms=3
    )
    self.ax_pdf_kappa.fill_between(
      self.bedges_log10_kappa,
      self.dict_log10_kappa["pdf"]["16p"],
      self.dict_log10_kappa["pdf"]["84p"],
      color="blue", ls="-", lw=2, alpha=0.25
    )
    self.ax_pdf_bnorm.plot(
      self.bedges_log10_bnorm,
      self.dict_log10_bnorm["pdf"]["50p"],
      color="blue", ls="-", marker="o", ms=3
    )
    self.ax_pdf_bnorm.fill_between(
      self.bedges_log10_bnorm,
      self.dict_log10_bnorm["pdf"]["16p"],
      self.dict_log10_bnorm["pdf"]["84p"],
      color="blue", ls="-", lw=2, alpha=0.25
    )
    ## marginalise the 2D distribution
    if BOOL_DEBUG:
      d_kappa = self.bedges_log10_kappa[1] - self.bedges_log10_kappa[0]
      d_bnorm = self.bedges_log10_bnorm[1] - self.bedges_log10_bnorm[0]
      pdf_log10_kappa = np.sum(d_bnorm * 10**np.array(self.dict_log10_kappa_bnorm["jpdf"]["50p"]), axis=1)
      pdf_log10_bnorm = np.sum(d_kappa * 10**np.array(self.dict_log10_kappa_bnorm["jpdf"]["50p"]), axis=0)
      self.ax_pdf_kappa.plot(
        self.bedges_log10_kappa[1:],
        np.log10(pdf_log10_kappa),
        color="red", ls="--", lw=1.5
      )
      self.ax_pdf_bnorm.plot(
        self.bedges_log10_bnorm[1:],
        np.log10(pdf_log10_bnorm),
        color="red", ls="--", lw=1.5
      )

  def _addAnotations(self):
    ## add colour bar
    cbar = PlotFuncs.addColorbar_fromCmap(
      fig        = self.fig,
      ax         = self.ax_jpdf_kappa_bnorm,
      cmap       = self.cmap,
      norm       = self.norm,
      cbar_title = r"$\log_{10}\big(\mathrm{PDF}(\kappa \ell_\mathrm{box}, b/b_\mathrm{rms})\big)$",
      cbar_title_pad=12, orientation="horizontal", size=5.5, fontsize=20
    )
    cbar.ax.tick_params(labelsize=16)
    ## log_10(kappa ell_box) = log_10(ell_box / R), where R = 1 / kappa = ell_box / factor -> log_10(factor)
    dict_line_params = { "ls":"--", "lw":1.5, "zorder":1 }
    self.ax_jpdf_kappa_bnorm.axvline(x=np.log10(2), color="black", **dict_line_params)
    self.ax_jpdf_kappa_bnorm.axhline(y=0, color="black", **dict_line_params)
    self.ax_pdf_kappa.axvline(x=np.log10(2), color="black", **dict_line_params)
    self.ax_pdf_bnorm.axvline(x=0, color="black", **dict_line_params)
    ## label axes
    self.ax_jpdf_kappa_bnorm.set_xlabel(r"$\log_{10}(\kappa \ell_{\rm box})$", fontsize=22)
    self.ax_jpdf_kappa_bnorm.set_ylabel(r"$\log_{10}(b / b_{\rm rms})$", fontsize=22)
    self.ax_pdf_kappa.set_xlabel(r"$\log_{10}(\kappa \ell_\mathrm{box} - \langle\kappa \ell_\mathrm{box}\rangle_\mathcal{V})$", fontsize=22)
    self.ax_pdf_bnorm.set_xlabel(r"$\log_{10}(b/b_\mathrm{rms} - \langle b/b_\mathrm{rms}\rangle_\mathcal{V})$", fontsize=22)
    self.ax_pdf_kappa.set_ylabel(r"$\log_{10}\big(\mathrm{PDF}(\kappa \ell_\mathrm{box})\big)$", fontsize=22)
    self.ax_pdf_bnorm.set_ylabel(r"$\log_{10}\big(\mathrm{PDF}(b/b_\mathrm{rms})\big)$", fontsize=22)
    # ## adjust axis bounds
    # bedge_kappa_lower, bedge_kappa_upper = setAxisLimits(self.ax_pdf_kappa, self.bedges_log10_kappa, self.dict_log10_kappa["pdf"]["50p"])
    # bedge_bnorm_lower, bedge_bnorm_upper = setAxisLimits(self.ax_pdf_bnorm, self.bedges_log10_bnorm, self.dict_log10_bnorm["pdf"]["50p"])
    # self.ax_jpdf_kappa_bnorm.set_xlim(bedge_kappa_lower, bedge_kappa_upper)
    # self.ax_jpdf_kappa_bnorm.set_ylim(bedge_bnorm_lower, bedge_bnorm_upper)
    ## for SSD sims. TODO: remove
    self.ax_jpdf_kappa_bnorm.set_xlim([-2.0, 4.0])
    self.ax_jpdf_kappa_bnorm.set_ylim([-3.0, 2.0])
    self.ax_pdf_kappa.set_xlim([-2.5, 5.0])
    self.ax_pdf_kappa.set_ylim([-8.0, 1.0])
    self.ax_pdf_bnorm.set_xlim([-4.0, 2.5])
    self.ax_pdf_bnorm.set_ylim([-8.0, 1.0])
    ## add annotations to joint pdf(kappa, bnorm)
    self.ax_jpdf_kappa_bnorm.text(
      0.05, 0.125,
      r"masked slope $=$ " + convertFloat2String(self.dict_log10_kappa_bnorm["masked-slope"]["50p"]),
      ha="left", va="bottom", fontsize=20, color="red", transform=self.ax_jpdf_kappa_bnorm.transAxes
    )
    plotLinePassingThroughPoint(
      ax     = self.ax_jpdf_kappa_bnorm,
      domain = [
        np.min(self.bedges_log10_kappa),
        np.max(self.bedges_log10_kappa)
      ],
      slope  = self.dict_log10_kappa_bnorm["masked-slope"]["50p"],
      coord  = [
        self.dict_log10_kappa["value"]["50p"],
        self.dict_log10_bnorm["value"]["50p"]
      ],
      color  = "red",
      ls     = "--",
      lw     = 1.5,
      zorder = 3
    )
    self.ax_jpdf_kappa_bnorm.text(
      0.05, 0.05,
      r"$\phi =$ " + convertFloat2String(self.dict_log10_kappa_bnorm["pearsonr"]["50p"]),
      ha="left", va="bottom", fontsize=20, color="orange", transform=self.ax_jpdf_kappa_bnorm.transAxes
    )
    plotLinePassingThroughPoint(
      ax     = self.ax_jpdf_kappa_bnorm,
      domain = [
        np.min(self.bedges_log10_kappa),
        np.max(self.bedges_log10_kappa)
      ],
      slope  = -1/2,
      coord  = [
        self.dict_log10_kappa["value"]["50p"],
        self.dict_log10_bnorm["value"]["50p"]
      ],
      color  = "black",
      ls     = ":",
      lw     = 1.5,
      zorder = 3
    )
    ## add annotations to marginal pdf(kappa)
    plotLinePassingThroughPoint(
      ax     = self.ax_pdf_kappa,
      domain = [
        np.min(self.bedges_log10_kappa),
        np.max(self.bedges_log10_kappa)
      ],
      slope  = 2.0,
      coord  = [self.dict_log10_kappa["value"]["50p"], 1.5],
      color  = "black",
      ls     = ":",
      lw     = 1.5,
      zorder = 3
    )
    plotLinePassingThroughPoint(
      ax     = self.ax_pdf_kappa,
      domain = [
        np.min(self.bedges_log10_kappa),
        np.max(self.bedges_log10_kappa)
      ],
      slope  = -5/2,
      coord  = [4, -4],
      color  = "black",
      ls     = "-.",
      lw     = 1.5,
      zorder = 3
    )
    plotLinePassingThroughPoint(
      ax     = self.ax_pdf_kappa,
      domain = [
        np.min(self.bedges_log10_kappa),
        np.max(self.bedges_log10_kappa)
      ],
      slope  = -13/7,
      coord  = [4, -5],
      color  = "black",
      ls     = "--",
      lw     = 1.5,
      zorder = 3
    )
    ## add annotations to marginal pdf(bnorm)
    plotLinePassingThroughPoint(
      ax     = self.ax_pdf_bnorm,
      domain = [
        np.min(self.bedges_log10_bnorm),
        np.max(self.bedges_log10_bnorm)
      ],
      slope  = 3.0,
      coord  = [self.dict_log10_bnorm["value"]["50p"], 0.5],
      color  = "black",
      ls     = ":",
      lw     = 1.5,
      zorder = 3
    )


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  start_time = time.time()
  obj_calc_stats = ComputeCurvatureStats()
  obj_calc_stats.performRoutine()
  WWTerminal.printLine(f"Total elapsed time: {time.time() - start_time:.2f} seconds")


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM