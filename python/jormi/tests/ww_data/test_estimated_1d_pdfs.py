## ###############################################################
## DEPENDENCIES
## ###############################################################
import numpy
from jormi.utils import list_utils
from jormi.ww_data import compute_stats
from jormi.ww_plots import plot_manager


## ###############################################################
## BINNING CONVERGENCE TEST
## ###############################################################
def main():
  num_samples = int(1e5)
  num_bins_to_test = [ 5, 10, 50, 100 ]
  pdfs_to_test = {
    "delta"       : numpy.random.normal(loc=10, scale=1e-9, size=num_samples),
    "uniform"     : numpy.random.uniform(low=0, high=1, size=num_samples),
    "normal"      : numpy.random.normal(loc=0, scale=1, size=num_samples),
    "exponential" : numpy.random.exponential(scale=1, size=num_samples),
  }
  integral_tolerance = 1e-2
  num_pdfs = len(pdfs_to_test)
  fig, axs = plot_manager.create_figure(num_rows=num_pdfs)
  if num_pdfs == 1: axs = list(axs)
  pdfs_that_failed = []
  for pdf_index, (pdf_label, pdf_samples) in enumerate(pdfs_to_test.items()):
    ax = axs[pdf_index]
    for num_bins in num_bins_to_test:
      bin_centers, estimated_pdf = compute_stats.estimate_pdf(pdf_samples, num_bins=num_bins, bin_range_percent=1.5)
      assert len(bin_centers) >= 3, f"Error: Bin centers for {pdf_label} with {num_bins} bins should have at least 3 bins, but got {len(bin_centers)}"
      assert bin_centers.shape == estimated_pdf.shape, f"Error: Mismatch in shapes of `bin_centers` ({bin_centers.shape}) and `estimated_pdf` ({estimated_pdf.shape}) for {pdf_label} with {num_bins} bins"
      if len(bin_centers) > 3: assert len(bin_centers) == num_bins, f"Error: The number of `bin_centers` ({len(bin_centers)}) does not match the expected number of bins ({num_bins}) for {pdf_label}"
      ax.step(bin_centers, estimated_pdf, where="mid", lw=2, label=f"{num_bins} bins")
      bin_widths = numpy.diff(bin_centers)
      bin_widths = numpy.append(bin_widths, bin_widths[-1])
      pdf_integral = numpy.sum(estimated_pdf * bin_widths)
      if abs(pdf_integral - 1.0) > integral_tolerance: pdfs_that_failed.append(pdf_label)
    ax.text(0.95, 0.95, pdf_label, ha="right", va="top", transform=ax.transAxes)
    ax.set_ylabel(r"PDF$(x)$")
  axs[-1].legend(loc="upper right", bbox_to_anchor=(1, 0.9), fontsize=20)
  axs[-1].set_xlabel(r"$x$")
  plot_manager.save_figure(fig, "estimated_1d_pdfs.png")
  assert len(pdfs_that_failed) == 0, f"Test failed for the following methods: {list_utils.cast_to_string(pdfs_that_failed)}"
  print("All tests passed successfully!")


## ###############################################################
## TEST ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()


## END OF TEST