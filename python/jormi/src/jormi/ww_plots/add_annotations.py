## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
from matplotlib.axes import Axes as mpl_axes
from matplotlib.lines import Line2D as mpl_line2d
from jormi.utils import list_utils


## ###############################################################
## FUNCTIONS
## ###############################################################
def add_text(
    ax          : mpl_axes,
    x_pos       : float,
    y_pos       : float,
    label       : str,
    x_alignment : str = "left",
    y_alignment : str = "top",
    fontsize    : float = 20,
    font_color  : str = "black",
    add_box     : bool = False,
    box_alpha   : float = 0.8,
    face_color  : str = "white",
    edge_color  : str = "black",
  ):
  valid_x_alignments = [ "left", "center", "right" ]
  valid_y_alignments = [ "top", "center", "bottom" ]
  if x_alignment not in valid_x_alignments: raise ValueError(f"`x_alignment` = `{x_alignment}` is not valid. Choose from: {list_utils.cast_to_string(valid_x_alignments)}")
  if y_alignment not in valid_y_alignments: raise ValueError(f"`y_alignment` = `{y_alignment}` is not valid. Choose from: {list_utils.cast_to_string(valid_y_alignments)}")
  box_params = None
  if add_box: box_params = dict(facecolor=face_color, edgecolor=edge_color, boxstyle="round,pad=0.3", alpha=box_alpha)
  ax.text(
    x_pos, y_pos, label,
    ha=x_alignment, va=y_alignment,
    color=font_color, fontsize=fontsize, transform=ax.transAxes, bbox=box_params
  )

def add_inset_axis(
    ax           : mpl_axes,
    bounds       : tuple[float, float, float, float] = (0.0, 1.0, 1.0, 0.5),
    x_label      : str | None = None,
    y_label      : str | None = None,
    fontsize     : float = 20,
    x_label_side : str = "left",
    y_label_side : str = "top",
  ):
  valid_x_sides = [ "top", "bottom" ]
  valid_y_sides = [ "left", "right" ]
  if x_label_side not in valid_x_sides: raise ValueError(f"`x_label_side` = `{x_label_side}` is invalid. Choose from: {list_utils.cast_to_string(valid_x_sides)}")
  if y_label_side not in valid_y_sides: raise ValueError(f"`y_label_side` = `{y_label_side}` is invalid. Choose from: {list_utils.cast_to_string(valid_y_sides)}")
  ax_inset = ax.inset_axes(bounds)
  ax_inset.set_xlabel(x_label, fontsize=fontsize)
  ax_inset.set_ylabel(y_label, fontsize=fontsize)
  ax_inset.xaxis.set_label_position(x_label_side)
  ax_inset.yaxis.set_label_position(y_label_side)
  ax_inset.tick_params(
      axis        = "x",
      labeltop    = (x_label_side == "top"),
      labelbottom = (x_label_side == "bottom"),
      top         = True,
      bottom      = True,
  )
  ax_inset.tick_params(
      axis        = "y",
      labelleft   = (y_label_side == "left"),
      labelright  = (y_label_side == "right"),
      left        = True,
      right       = True,
  )
  return ax_inset

def add_custom_legend(
    ax             : mpl_axes,
    artists        : list[str],
    labels         : list[str],
    colors         : list[str],
    marker_size    : float = 8,
    line_width     : float = 1.5,
    fontsize       : float = 16,
    text_color     : str = "black",
    position       : str = "upper right",
    anchor         : tuple[float, float] = (1.0, 1.0),
    enable_frame   : bool = False,
    frame_alpha    : float = 0.5,
    num_cols       : float = 1,
    text_padding   : float = 0.5,
    label_spacing  : float = 0.5,
    column_spacing : float = 0.5,
  ):
  artists_to_draw = []
  valid_markers   = [ ".", "o", "s", "D", "^", "v" ]
  valid_lines     = [ "-", "--", "-.", ":" ]
  for artist, color in zip(artists, colors):
    if artist in valid_markers: artist_to_draw = mpl_line2d([0], [0], marker=artist, color=color, linewidth=0, markeredgecolor="black", markersize=marker_size)
    elif artist in valid_lines: artist_to_draw = mpl_line2d([0], [0], linestyle=artist, color=color, linewidth=line_width)
    else: raise ValueError(
      f"Artist = `{artist}` is not a recognized marker or line style.\n"
      f"\t> Valid markers: {list_utils.cast_to_string(valid_markers)}.\n"
      f"\t> Valid line styles: {list_utils.cast_to_string(valid_lines)}."
    )
    artists_to_draw.append(artist_to_draw)
  legend = ax.legend(
    artists_to_draw,
    labels,
    bbox_to_anchor = anchor,
    loc            = position,
    fontsize       = fontsize,
    labelcolor     = text_color,
    frameon        = enable_frame,
    framealpha     = frame_alpha,
    facecolor      = "white",
    edgecolor      = "grey",
    ncol           = num_cols,
    borderpad      = 0.45,
    handletextpad  = text_padding,
    labelspacing   = label_spacing,
    columnspacing  = column_spacing,
  )
  ax.add_artist(legend)


## END OF MODULE