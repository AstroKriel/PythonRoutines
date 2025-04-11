import sys
import numpy
from jormi.ww_io import flash_data
from jormi.ww_plots import plot_manager


class PlotVIData():
  def __init__(self, directory):
    self.directory = directory

  def run(self):
    fig, axs = plot_manager.create_figure(num_rows=3, share_x=True)
    self._load_data()
    self._plot_data(axs)
    plot_manager.save_figure(fig, "demo_vi_plot.png")

  def _load_data(self):
    self.time, self.mach_number = flash_data.read_vi_data(directory=self.directory, dataset_name="mach")
    _, self.kinetic_energy  = flash_data.read_vi_data(directory=self.directory, dataset_name="kin")
    _, self.magnetic_energy = flash_data.read_vi_data(directory=self.directory, dataset_name="mag")

  def _plot_data(self, axs):
    plot_params = dict(marker="o", ms=5, ls="-", lw=2.0)
    axs[0].plot(self.time, self.mach_number, color="black", **plot_params)
    axs[1].plot(self.time, numpy.log10(self.kinetic_energy), color="blue", **plot_params)
    axs[2].plot(self.time, numpy.log10(self.magnetic_energy), color="red", **plot_params)


def main():
  routine = PlotVIData()
  routine.run()


if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF SCRIPT