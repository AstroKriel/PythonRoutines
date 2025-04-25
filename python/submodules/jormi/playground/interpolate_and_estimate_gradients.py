## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
from jormi.ww_plots import plot_manager
from jormi.ww_data import interpolate_data


## ###############################################################
## HELPER FUNCTION
## ###############################################################
def generate_data(num_points):
    x_data       = numpy.linspace(-5, 15, num=num_points, endpoint=True)
    y_exact      = numpy.cos(-numpy.square(x_data) / 9.0)
    dydx_exact   = - (2.0 / 9.0) * x_data * numpy.sin(numpy.square(x_data) / 9.0)
    d2ydx2_exact = - (2.0 / 9.0) * numpy.sin(numpy.square(x_data) / 9.0) \
                   - numpy.square((2.0 / 9.0) * x_data) * numpy.cos(numpy.square(x_data) / 9.0)
    return x_data, y_exact, dydx_exact, d2ydx2_exact


## ###############################################################
## DEMO INTERPOLATING DATA
## ###############################################################
def main():
  x_data, y_data, dydx_exact, d2ydx2_exact = generate_data(25)
  x_interp = numpy.linspace(x_data.min(), x_data.max(), 50)
  fig, axs = plot_manager.create_figure(num_rows=3, share_x=True, axis_shape=(5, 8))
  plot_style_approx = { "color":"black", "ls":"", "marker":"o", "ms":10, "zorder":5, "label":"raw data" }
  axs[0].plot(x_data, y_data,       **plot_style_approx)
  axs[1].plot(x_data, dydx_exact,   **plot_style_approx)
  axs[2].plot(x_data, d2ydx2_exact, **plot_style_approx)
  for (interp_method, color) in [
      ("linear", "red"),
      ("quadratic", "green"),
      ("cubic", "blue"),
    ]:
    _, y_interp   = interpolate_data.interpolate_1d(x_data, y_data, x_interp, kind=interp_method)
    dydx_interp   = numpy.gradient(y_interp, x_interp)
    d2ydx2_interp = numpy.gradient(dydx_interp, x_interp)
    plot_style_approx = { "color":color, "ls":"-", "lw":1.5, "marker":"o", "ms":5, "zorder":3, "label":f"interp1d ({interp_method})" }
    axs[0].plot(x_interp, y_interp,      **plot_style_approx)
    axs[1].plot(x_interp, dydx_interp,   **plot_style_approx)
    axs[2].plot(x_interp, d2ydx2_interp, **plot_style_approx)
  axs[0].set_ylabel("y-values")
  axs[1].set_ylabel("first derivatives")
  axs[2].set_ylabel("second derivatives")
  axs[2].set_xlabel("x-values")
  axs[1].axhline(y=0, ls="--", color="black", zorder=1)
  axs[2].axhline(y=0, ls="--", color="black", zorder=1)
  axs[1].legend(loc="upper left")
  plot_manager.save_figure(fig, "interpolate_and_estimate_gradients.png")


## ###############################################################
## SCRIPT ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()


## END OF SCRIPT