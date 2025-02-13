import os, sys, math


## ###############################################################
## GLOBAL PARAMETERS
## ###############################################################
BOOL_VERBOSE = False

## ###############################################################
## HELPER FUNCTION
## ###############################################################
def readOutputFile(filepath):
  print("Reading:", filepath)
  with open(filepath, "r") as fp:
    return fp.readlines()

def processLine(line_index, line):
  if (line_index % 100) == 0: print("x", end="")
  if (line_index % 500) == 499: print(" ", end="")
  if "no-file" in line: return line
  if "read" in line: return line
  if "deleted" in line: return line
  if "/" not in line: return line
  filepath = line.strip().split()[-1]
  if any([
      elem in filepath
      for elem in [
        ".sh", ".out", ".png", ".pdf", ".o1", ".lock"
      ]
    ]):
    return deleteFile(filepath, line)
  elif any([
      elem in filepath
      for elem in [
        "flash", ".dat", ".log", "driving.par", "driving_history.txt", "_chk_", ".json", ".h5", ".code-workspace",
      ]
    ]):
    return readFile(filepath, line)
  return f"check. {line.strip()}\n"

def deleteFile(filepath, original_line):
  if os.path.isfile(filepath):
    try:
      os.remove(filepath)
      return f"deleted. {original_line.strip()}\n"
    except Exception as e:
      if BOOL_VERBOSE: print(f"Error deleting file {filepath}: {e}")
      return f"error. {original_line.strip()}\n"
  else:
    if BOOL_VERBOSE: print(f"Not a file or doesn't exist: {filepath}")
    return f"no-file. {original_line.strip()}\n"

def readFile(filepath, original_line):
  if os.path.isfile(filepath):
    try:
      with open(filepath, "rb") as fp:
        fp.read(10)
      return f"read. {original_line.strip()}\n"
    except Exception as e:
      if BOOL_VERBOSE: print(f"Error deleting file {filepath}: {e}")
      return f"error. {original_line.strip()}\n"
  else:
    if BOOL_VERBOSE: print(f"Not a file or doesn't exist: {filepath}")
    return f"no-file. {original_line.strip()}\n"

def writeOutputFile(filepath, lines):
  with open(filepath, "w") as fp:
    fp.writelines(lines)
  print("\nSaved:", filepath)


## ###############################################################
## MAIN FUNCTION
## ###############################################################
def processOutputFile(filepath_file):
  print(f"Looking at:", filepath_file)
  try:
    list_lines = readOutputFile(filepath_file)
    list_updated_lines = [
      processLine(line_index, line)
      for line_index, line in enumerate(list_lines)
    ]
    writeOutputFile(filepath_file, list_updated_lines)
  except FileNotFoundError: print(f"File not found: {filepath_file}")
  except Exception as e: print(f"An error occurred: {e}")
  print("Finished.\n")


## ###############################################################
## SCRIPT ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  directory_home = "/home/586/nk7952"
  processOutputFile(f"{directory_home}/files_quarantined.txt")
  processOutputFile(f"{directory_home}/files_warned.txt")
  sys.exit(0)

## END OF SCRIPT