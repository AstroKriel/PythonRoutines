import matplotlib.pyplot as mpl_plot
from matplotlib import rcParams

mpl_plot.switch_backend("agg")

## default font sizes
FONT_SIZES = {
  "small"  : 16,
  "medium" : 20,
  "large"  : 25,
}

rcParams.update({
  ## LaTeX support
  "text.usetex" : True,
  "text.latex.preamble" : r"\usepackage{bm, amsmath, mathrsfs, amssymb, url, xfrac}",

  ## font settings
  "font.family"      : "serif",
  "font.size"        : FONT_SIZES["large"],
  "axes.titlesize"   : FONT_SIZES["large"],
  "axes.labelsize"   : FONT_SIZES["large"],
  "xtick.labelsize"  : FONT_SIZES["medium"],
  "ytick.labelsize"  : FONT_SIZES["medium"],
  "legend.fontsize"  : FONT_SIZES["medium"],
  "figure.titlesize" : FONT_SIZES["small"],

  ## line styles
  "lines.linewidth": 1.2,
  "axes.linewidth": 0.8,

  ## axis-tick settings
  "xtick.top": True, "ytick.right": True,
  "xtick.direction": "in", "ytick.direction": "in",
  "xtick.minor.visible": True, "ytick.minor.visible": True,
  "xtick.major.size": 6, "ytick.major.size": 6,
  "xtick.minor.size": 3, "ytick.minor.size": 3,
  "xtick.major.width": 0.75, "ytick.major.width": 0.75,
  "xtick.minor.width": 0.75, "ytick.minor.width": 0.75,
  "xtick.major.pad": 5, "ytick.major.pad": 5,
  "xtick.minor.pad": 5, "ytick.minor.pad": 5,

  ## legend
  "legend.fontsize": FONT_SIZES["medium"],
  "legend.labelspacing": 0.2,
  "legend.loc": "upper right",
  "legend.frameon": False,

  ## figure and saving settings
  "figure.figsize": (8.0, 5.0),
  "savefig.dpi": 200, # resolution
  "savefig.bbox": "tight",
  "savefig.transparent": False,
  "savefig.pad_inches": 0.1, # padding around figure when saving
})

## END OF PARAMETERS