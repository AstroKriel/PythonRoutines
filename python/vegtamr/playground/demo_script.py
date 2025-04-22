## This file is part of the "Vegtamr" project.
## Copyright (c) 2024 Neco Kriel.
## Licensed under the MIT License. See LICENSE for details.


## ###############################################################
## DEPENDENCIES
## ###############################################################
import sys
import numpy
import matplotlib.pyplot as mpl_plot
from vegtamr.lic import compute_lic_with_postprocessing
from vegtamr.utils import vfields


## ###############################################################
## HELPER FUNCTION
## ###############################################################
def plot_lic(
    ax                  : mpl_plot.Axes,
    sfield              : numpy.ndarray,
    vfield              : numpy.ndarray,
    bounds_rows         : tuple[float, float] = None,
    bounds_cols         : tuple[float, float] = None,
    overlay_streamlines : bool = False,
  ):
  ax.imshow(
    sfield,
    cmap   = "bone",
    origin = "lower",
    extent = [
      bounds_rows[0], bounds_rows[1],
      bounds_cols[0], bounds_cols[1]
    ],
  )
  if overlay_streamlines:
    coords_row = numpy.linspace(bounds_rows[0], bounds_rows[1], sfield.shape[0])
    coords_col = numpy.linspace(bounds_cols[0], bounds_cols[1], sfield.shape[1])
    mg_x, mg_y = numpy.meshgrid(coords_col, coords_row, indexing="xy")
    ax.streamplot(
      mg_x, mg_y,
      vfield[0], vfield[1],
      color              = "white",
      arrowstyle         = "->",
      linewidth          = 1.0,
      density            = 0.5,
      arrowsize          = 0.5,
      broken_streamlines = False,
    )
  ax.set_xticks([])
  ax.set_yticks([])
  ax.set_xlim(bounds_rows)
  ax.set_ylim(bounds_cols)


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  print("Started running demo script...")
  size         = 500
  vfield_dict  = vfields.vfield_flowers(size)
  vfield       = vfield_dict["vfield"]
  streamlength = vfield_dict["streamlength"]
  bounds_rows  = vfield_dict["bounds_rows"]
  bounds_cols  = vfield_dict["bounds_cols"]
  vfield_name  = vfield_dict["name"]
  print("Computing LIC...")
  ## apply the LIC multiple times: equivelant to applying several passes with a paint brush.
  ## note: `backend` options include "python" (implemented in this project) or "rust" (2-10x faster; https://github.com/tlorach/rLIC)
  sfield = compute_lic_with_postprocessing(
    vfield                 = vfield,
    streamlength           = streamlength,
    num_lic_passes         = 1,
    num_postprocess_cycles = 1,
    use_filter             = False,
    filter_sigma           = 2.0, # rouhly the pixel-width of LIC tubes
    use_equalize           = False,
    backend                = "rust",
  )
  print("Plotting data...")
  fig, ax = mpl_plot.subplots(figsize=(6, 6))
  fig, _ = plot_lic(
    ax                  = ax,
    sfield              = sfield,
    vfield              = vfield,
    bounds_rows         = bounds_rows,
    bounds_cols         = bounds_cols,
    overlay_streamlines = False,
  )
  print("Saving figure...")
  fig_name = f"lic_{vfield_name}.png"
  fig.savefig(fig_name, dpi=300, bbox_inches="tight")
  mpl_plot.close(fig)
  print("Saved:", fig_name)


## ###############################################################
## SCRIPT ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF SCRIPT
