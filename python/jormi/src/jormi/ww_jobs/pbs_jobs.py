## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
from jormi.ww_io import file_manager, shell_manager


## ###############################################################
## FUNCTIONS
## ###############################################################
def submit_job(
    directory    : str,
    file_name     : str,
    check_status : bool = False,
  ) -> bool:
  if check_status and is_job_already_in_queue(directory, file_name):
    print("Job is already currently running:", file_name)
    return False
  print("Submitting job:", file_name)
  try:
    shell_manager.execute_shell_command(f"qsub {file_name}", working_directory=directory, enforce_shell=True)
    return True
  except RuntimeError as error:
    print(f"Failed to submit job `{file_name}`: {error}")
    return False

def is_job_already_in_queue(
    directory : str,
    file_name : str,
  ) -> bool:
  """Checks if a job name is already in the queue."""
  file_path = file_manager.combine_file_path_parts([directory, file_name])
  if not file_manager.does_file_exist(file_path=file_path):
    print(f"`{file_name}` job file does not exist in: {directory}")
    return False
  job_tagname = get_job_name_from_pbs_script(file_path)
  if not job_tagname:
    print(f"`#PBS -N` not found in job file: {file_name}")
    return False
  job_tagnames = get_list_of_queued_jobs()
  if not job_tagnames: return False
  return job_tagname in job_tagnames

def get_job_name_from_pbs_script(file_path : str) -> str | None:
  """Gets the job name from a PBS job script."""
  with open(file_path, "r") as file_pointer:
    for line in file_pointer:
      if "#PBS -N" in line:
        return line.strip().split(" ")[-1] if line.strip() else None
  return None

def get_list_of_queued_jobs() -> list[str] | None:
  """Collects all job names currently in the queue."""
  try:
    raw_output = shell_manager.execute_shell_command("qstat -f | grep Job_Name", capture_output=True)
    ## extract job names
    job_names = [
        line.strip().split()[-1] # assumes that the last word on each line is the job name
        for line in raw_output.split("\n")
        if line.strip() # ignore empty or whitespace-only lines
    ]
    return job_names if job_names else []
  except RuntimeError as error:
    print(f"Error retrieving job names from the queue: {error}")
    return None



## END OF MODULE