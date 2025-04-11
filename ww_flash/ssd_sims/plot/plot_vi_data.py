import sys
from loki.ww_io.flash_data import read_vi_data

def main():
  time_values, mach_values = read_vi_data.read_vi_data(
    directory    = "/scratch/jh2/nk7952/Re1500/Mach0.1/Pm1/144",
    dataset_name = "mach"
  )

if __name__ == "__main__":
  main()
  sys.exit(0)

