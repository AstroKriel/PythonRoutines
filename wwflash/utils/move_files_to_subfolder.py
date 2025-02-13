#!/usr/bin/env python3

## ###############################################################
## MODULES
## ###############################################################
import sys

## load user defined modules
from TheUsefulModule import WWArgparse, WWFnF, WWTerminal


## ###############################################################
## MAIN PROGRAM
## ###############################################################
def main():
  parser = WWArgparse.MyParser(description="Restart simulation.")
  ## ------------------- DEFINE OPTIONAL ARGUMENTS
  args_opt = parser.add_argument_group(description="Optional processing arguments:")
  args_opt.add_argument("-move",                **WWArgparse.OPT_BOOL_ARG, default=False)
  args_opt.add_argument("-sub_folder",          **WWArgparse.OPT_ARG, type=str, default="subset")
  args_opt.add_argument("-files_per_tturb",     **WWArgparse.OPT_ARG, type=int, default=10)
  args_opt.add_argument("-move_every_nth_file", **WWArgparse.OPT_ARG, type=int, default=1)
  ## ------------------- DEFINE REQUIRED ARGUMENTS
  args_req = parser.add_argument_group(description="Required processing arguments:")
  args_req.add_argument("-directory_from", type=str, required=True, help="type: %(type)s")
  args_req.add_argument("-start_time",     type=int, required=True, help="type: %(type)s")
  args_req.add_argument("-end_time",       type=int, required=True, help="type: %(type)s")
  print(" ")
  ## open arguments
  args = vars(parser.parse_args())
  ## save parameters
  bool_debug          = not(args["move"])
  directory_from      = args["directory_from"]
  start_time          = int(args["start_time"])
  end_time            = int(args["end_time"])
  sub_folder          = args["sub_folder"]
  files_per_tturb     = int(args["files_per_tturb"])
  move_every_nth_file = int(args["move_every_nth_file"])
  ## move files
  if bool_debug: print("Running in debug mode.")
  else: WWFnF.createDirectory(f"{directory_from}/{sub_folder}")
  list_files_in_directory= WWFnF.getFilesInDirectory(
    directory             = directory_from,
    filename_starts_with  = "Turb",
    filename_contains     = "plt_",
    filename_not_contains = "spect_",
    loc_file_index        = 4,
    file_start_index      = start_time * files_per_tturb,
    file_end_index        = end_time * files_per_tturb,
  )
  print(f"Moving {len(list_files_in_directory[::move_every_nth_file])} files:")
  print(f"\t> from: {directory_from}/")
  print(f"\t> to:   {directory_from}/{sub_folder}/")
  print(f"\t> between t/t_turb \in [{start_time}, {end_time}]")
  print(f"\t> only moving every {move_every_nth_file}-th file")
  print(f"\t> with {files_per_tturb} files per t/t_turb")
  print(" ")
  for filename in list_files_in_directory[::move_every_nth_file]:
    WWTerminal.runCommand(
      command    = f"mv {filename} {sub_folder}/.",
      directory  = directory_from,
      bool_debug = bool_debug
    )


## ###############################################################
## PROGRAM ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  main()
  sys.exit(0)


## END OF PROGRAM