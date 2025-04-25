import sys
import time
import numpy
from jormi.ww_io import flash_data, file_manager
from jormi.ww_plots import plot_manager
from jormi.ww_fields import compute_spectra

from aux_funcs import power_spectra_funcs

def time_function(func, *args, repeats=3, label="Function"):
  durations = []
  for _ in range(repeats):
    start = time.perf_counter()
    func(*args)
    end = time.perf_counter()
    durations.append(end - start)
  avg_time = sum(durations) / len(durations)
  print(f"{label}: Average execution time over {repeats} runs: {avg_time:.5f} seconds")
  return avg_time

def main():
  directory = "/scratch/ek9/nk7952/Re1500/Mach0.8/Pm1/288/plt/"
  file_name = "Turb_hdf5_plt_cnt_0069"
  file_path = file_manager.create_file_path([ directory, file_name ])
  field = flash_data.read_flash_field(file_path=file_path, dataset_name="mag")
  if len(field.shape) > 3: _field = field
  else: _field = numpy.array([field])
  def _method1():
    compute_spectra.compute_1d_power_spectrum(field)
  def _method2():
    spectrum_3d = power_spectra_funcs.compute_power_spectrum_3D(_field)
    power_spectra_funcs.spherical_integrate(spectrum_3d)
  time_function(_method2, label="Method 2 (aux_funcs)")
  time_function(_method1, label="Method 1 (compute_spectra)")
  time_function(_method2, label="Method 2 (aux_funcs)")
  time_function(_method1, label="Method 1 (compute_spectra)")
  time_function(_method1, label="Method 1 (compute_spectra)")
  time_function(_method2, label="Method 2 (aux_funcs)")
  k_modes, power_spectrum = compute_spectra.compute_1d_power_spectrum(field)
  spectrum_3d = power_spectra_funcs.compute_power_spectrum_3D(_field)
  _k_modes, _power_spectrum = power_spectra_funcs.spherical_integrate(spectrum_3d)
  fig, ax = plot_manager.create_figure()
  ax.plot(
    k_modes,
    power_spectrum,
    color="blue", ls="-", lw=2.5, marker="o", ms=5
  )
  ax.plot(
    _k_modes,
    _power_spectrum,
    color="red", ls="-", lw=1.0, marker="o", ms=2
  )
  ax.set_xscale("log")
  ax.set_yscale("log")
  plot_manager.save_figure(fig, "demo_power_spectrum.png")

if __name__ == "__main__":
  main()
  sys.exit(0)

