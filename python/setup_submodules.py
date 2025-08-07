import os
import sys
import argparse
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

SUBMODULES = {
  "arepo"   : SCRIPT_DIR / "ww_arepo_sims",
  "flash"   : SCRIPT_DIR / "ww_flash_sims",
  "quokka"  : SCRIPT_DIR / "ww_quokka_sims",
  "bifrost" : SCRIPT_DIR / "submodules/bifrost",
  "jormi"   : SCRIPT_DIR / "submodules/jormi",
  "vegtamr" : SCRIPT_DIR / "submodules/vegtamr",
}

def parse_args():
  parser = argparse.ArgumentParser(description="Link selected sindri submodules into a project-env managed by uv.")
  parser.add_argument("target_dir", type=Path, help="Target project directory (must contain a pyproject.toml)")
  for module_name in SUBMODULES:
    parser.add_argument(f"--{module_name}", action="store_true", help=f"Link python submodule `{module_name}`")
  parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
  return parser.parse_args()

def link_editable(
    target_dir  : Path,
    module_name : str,
    dry_run     : bool = False
  ):
  ## make sure the project directory has a pyproject.toml file
  pyproject_path = target_dir / "pyproject.toml"
  if not pyproject_path.exists():
    print(f"Error: no pyproject.toml found in {target_dir}")
    sys.exit(1)
  ## switch working directory to the target project (so uv uses the correct env context)
  os.chdir(target_dir)
  ## confirm the requested module exists
  module_path = SUBMODULES.get(module_name)
  if not module_path:
    print(f"Warning: unknown module `{module_name}`")
    return
  if not module_path.exists():
    print(f"Warning: `{module_name}` could not be found under: {module_path}")
    return
  ## link (editable install) the module
  command = ["uv", "pip", "install", "-e", str(module_path)]
  if dry_run:
    print(f"[dry-run] Would link `{module_name}` from: {module_path}")
  else:
    print(f"Linking `{module_name}` from: {module_path}")
    try:
      subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
      print(f"Error: failed to link `{module_name}`: {e}")

def main():
  ## parse user inputs
  user_args = parse_args()
  selected_modules = [
    module_name
    for module_name in SUBMODULES
    if getattr(user_args, module_name)
  ]
  if not selected_modules:
    print("No modules selected. Available flags:")
    print("  " + " ".join(f"--{module_name}" for module_name in SUBMODULES))
    sys.exit(1)
  ## confirm target project directory
  target_dir = user_args.target_dir.resolve()
  dry_run = user_args.dry_run
  if not target_dir.exists():
    raise FileNotFoundError(f"Target project directory does not exist: {target_dir}")
  print(f"Target project directory: {target_dir}")
  user_response = input("Is this correct? [y/N]: ").strip().lower()
  if user_response not in ("y", "yes"):
    print("Aborting.")
    sys.exit(1)
  for module_name in selected_modules:
    link_editable(target_dir, module_name, dry_run)

if __name__ == "__main__":
  main()

## .