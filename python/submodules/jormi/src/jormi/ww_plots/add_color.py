## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import cmasher
import matplotlib.colors as mpl_colors


## ###############################################################
## FUNCTIONS
## ###############################################################
def create_norm(
    vmin : float = 0.0,
    vmid : float = None,
    vmax : float = 1.0,
  ):
  if vmid is not None:
    return mpl_colors.TwoSlopeNorm(vmin=vmin, vcenter=vmid, vmax=vmax)
  else: return mpl_colors.Normalize(vmin=vmin, vmax=vmax)

def create_cmap(
    cmap_name: str,
    cmin: float = 0.0,
    cmax: float = 1.0,
    vmin: float = 0.0,
    vmid: float = None,
    vmax: float = 1.0,
  ):
  cmap = cmasher.get_sub_cmap(cmap_name, cmin, cmax)
  norm = create_norm(vmin=vmin, vmid=vmid, vmax=vmax)
  return cmap, norm

def add_cbar_from_cmap(
    ax, cmap, norm,
    label         : str = "",
    side          : str = "right",
    percentage    : float = 0.1,
    cbar_padding  : float = 0.02,
    label_padding : float = 10,
    fontsize      : float = 20,
  ):
  fig = ax.figure
  box = ax.get_position()
  if side in [ "left", "right" ]:
    orientation = "vertical"
    cbar_size = box.width * percentage
    if side == "right":
      cbar_bounds = [ box.x1 + cbar_padding, box.y0, cbar_size, box.height ]
    else: cbar_bounds = [ box.x0 - cbar_size - cbar_padding, box.y0, cbar_size, box.height ]
  elif side in [ "top", "bottom" ]:
    orientation = "horizontal"
    cbar_size = box.height * percentage
    if side == "top":
      cbar_bounds = [ box.x0, box.y1 + cbar_padding, box.width, cbar_size ]
    else: cbar_bounds = [ box.x0, box.y0 - cbar_size - cbar_padding, box.width, cbar_size ]
  else: raise ValueError(f"Unsupported side: {side}")
  ax_cbar = fig.add_axes(cbar_bounds)
  cbar = fig.colorbar(mappable=None, cmap=cmap, norm=norm, cax=ax_cbar, orientation=orientation)
  if orientation == "horizontal":
    cbar.ax.set_title(label, fontsize=fontsize, pad=label_padding)
    cbar.ax.xaxis.set_ticks_position(side)
  else:
    cbar.set_label(label, fontsize=fontsize, rotation=-90, va="bottom")
    cbar.ax.yaxis.set_ticks_position(side)
  return cbar


## END OF MODULE