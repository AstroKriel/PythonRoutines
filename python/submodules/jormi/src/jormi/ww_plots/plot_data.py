## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
import matplotlib.axes as mpl_axes
from matplotlib.collections import LineCollection
from jormi.ww_plots import add_color


## ###############################################################
## FUNCTIONS
## ###############################################################
def plot_wo_scaling_axis(
    ax      : mpl_axes.Axes,
    x_data  : list[float] | numpy.ndarray,
    y_data  : list[float] | numpy.ndarray,
    color   : str = "black",
    ls      : str = ":",
    lw      : float = 1,
    label   : str | None = None,
    alpha   : float = 1.0,
    zorder  : float = 1
  ):
  x_data = numpy.asarray(x_data)
  y_data = numpy.asarray(y_data)
  if x_data.ndim != 1: raise ValueError(f"`x_data` must be 1D. Got shape {x_data.shape}.")
  if y_data.ndim != 1: raise ValueError(f"`y_data` must be 1D. Got shape {y_data.shape}.")
  if x_data.shape != y_data.shape:
    raise ValueError(f"`x_data` and `y_data` must have the same shape. {x_data.shape} != {y_data.shape}.")
  collection = LineCollection(
    [ numpy.column_stack((x_data, y_data)) ],
    colors     = color,
    linestyles = ls,
    linewidths = lw,
    alpha      = alpha,
    zorder     = zorder,
    label      = label
  )
  ax.add_collection(collection, autolim=False)

def plot_sfield_slice(
    ax,
    field_slice  : numpy.ndarray,
    axis_bounds  : tuple[float, float, float, float] = (-1, 1, -1, 1),
    cbar_bounds  : tuple[float, float] = None,
    cmap_name    : str = "cmr.arctic",
    add_colorbar : bool = True,
    cbar_label   : str = None,
    cbar_side    : str = "right",
  ):
  if field_slice.ndim != 2: raise ValueError("`field_slice` must be a 2D array.")
  vmin = 0.9 * numpy.min(field_slice) if (cbar_bounds is None) else cbar_bounds[0]
  vmax = 1.1 * numpy.max(field_slice) if (cbar_bounds is None) else cbar_bounds[1]
  cmap, norm = add_color.create_cmap(
    cmap_name = cmap_name,
    vmin      = vmin,
    vmax      = vmax,
  )
  im_obj = ax.imshow(
    field_slice,
    extent = axis_bounds,
    cmap   = cmap,
    norm   = norm
  )
  ax.set_xlim([ axis_bounds[0], axis_bounds[1] ])
  ax.set_ylim([ axis_bounds[2], axis_bounds[3] ])
  if add_colorbar:
    add_color.add_cbar_from_cmap(
      ax    = ax,
      cmap  = cmap,
      norm  = norm,
      label = cbar_label,
      side  = cbar_side,
    )
  return im_obj

def _generate_grid(field_shape, axis_bounds):
  if not (isinstance(axis_bounds, tuple) and len(axis_bounds) == 4 and all(isinstance(value, (int, float)) for value in axis_bounds)):
    raise ValueError("`axis_bounds` must be a tuple of four floats.")
  coords_row = numpy.linspace(axis_bounds[0], axis_bounds[1], field_shape[0])
  coords_col = numpy.linspace(axis_bounds[2], axis_bounds[3], field_shape[1])
  grid_x, grid_y = numpy.meshgrid(coords_col, coords_row, indexing="xy")
  return grid_x, grid_y

def plot_vfield_slice_quiver(
    ax,
    field_slice_rows : numpy.ndarray,
    field_slice_cols : numpy.ndarray,
    axis_bounds      : tuple[float, float, float, float] = (-1.0, 1.0, -1.0, 1.0),
    num_quivers      : int = 25,
    quiver_width     : float = 5e-3,
    field_color      : str = "white",
  ):
  if field_slice_rows.shape != field_slice_cols.shape:
    raise ValueError("`field_slice_rows` and `field_slice_cols` must have the same shape.")
  grid_x, grid_y = _generate_grid(field_slice_rows.shape, axis_bounds)
  quiver_step_rows = max(1, field_slice_rows.shape[0] // num_quivers)
  quiver_step_cols = max(1, field_slice_cols.shape[1] // num_quivers)
  field_slice_xrows_subset = field_slice_rows[::quiver_step_rows, ::quiver_step_cols]
  field_slice_xcols_subset = field_slice_cols[::quiver_step_rows, ::quiver_step_cols]
  ax.quiver(
    grid_x[::quiver_step_rows, ::quiver_step_cols],
    grid_y[::quiver_step_rows, ::quiver_step_cols],
    field_slice_xcols_subset,
    field_slice_xrows_subset,
    width = quiver_width,
    color = field_color
  )
  ax.set_xlim([ axis_bounds[0], axis_bounds[1] ])
  ax.set_ylim([ axis_bounds[2], axis_bounds[3] ])

def plot_vfield_slice_streamplot(
    ax,
    field_slice_rows     : numpy.ndarray,
    field_slice_cols     : numpy.ndarray,
    axis_bounds          : tuple[float, float, float, float] = (-1.0, 1.0, -1.0, 1.0),
    streamline_weights   : numpy.ndarray = None,
    streamline_width     : float = None,
    streamline_scale     : float = 1.5,
    streamline_linestyle : str = "-",
    field_color          : str = "white",
  ):
  if field_slice_rows.shape != field_slice_cols.shape:
    raise ValueError("`field_slice_rows` and `field_slice_cols` must have the same shape.")
  grid_x, grid_y = _generate_grid(field_slice_rows.shape, axis_bounds)
  if streamline_width is None:
    if streamline_weights is None: streamline_width = 1
    elif streamline_weights.shape != field_slice_cols.shape:
      raise ValueError("`streamline_weights` must have the same shape as field slices.")
    else: streamline_width = streamline_scale * (1 + streamline_weights / numpy.max(streamline_weights))
  ax.streamplot(
    grid_x,
    grid_y,
    field_slice_cols,
    field_slice_rows,
    color     = field_color,
    linewidth = streamline_width,
    density   = 2.0,
    arrowsize = 1.0,
    linestyle = streamline_linestyle,
  )
  ax.set_xlim([ axis_bounds[0], axis_bounds[1] ])
  ax.set_ylim([ axis_bounds[2], axis_bounds[3] ])


## END OF MODULE