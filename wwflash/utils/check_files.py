import glob

base_dir = '/scratch/jh2/nk7952/R*/Mach*/Pm*/*/'
list_filepaths_inputs = [
  filepath.split("sim_")[0]
  for filepath in glob.glob(f"{base_dir}/sim_inputs.json")
]
list_filepaths_outputs = [
  filepath.split("sim_")[0]
  for filepath in glob.glob(f"{base_dir}/sim_outputs.h5")
]
for filepath in list_filepaths_inputs:
  if filepath not in list_filepaths_outputs:
    print(filepath)
