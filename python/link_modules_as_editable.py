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

GITHUB_REPOS = {
  "arepo"   : "ww_arepo_sims @ git+https://github.com/AstroKriel/WWArepoSims",
  "flash"   : "ww_flash_sims @ git+https://github.com/AstroKriel/WWFlashSims",
  "quokka"  : "ww_quokka_sims @ git+https://github.com/AstroKriel/WWQuokkaSims",
  "bifrost" : "bifrost @ git+https://github.com/AstroKriel/HDF5DataManager",
  "jormi"   : "jormi @ git+https://github.com/AstroKriel/PythonTools",
  "vegtamr" : "vegtamr @ git+https://github.com/AstroKriel/LineIntegralConvolution",
}

def parse_args():
  parser = argparse.ArgumentParser(description="Link selected sindri submodules into a project-env managed by uv.")
  parser.add_argument("target_dir", type=Path, help="Target project directory (must contain a pyproject.toml)")
  for module_name in sorted(SUBMODULES):
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
  if not module_path or not module_path.exists():
    print(f"Error: `{module_name}` could not be found under: {module_path}")
    sys.exit(1)
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

def write_dependency_notice(target_dir, selected_modules):
  file_path = target_dir / "DEPENDENCY_NOTICE.txt"
  file_content = []
  file_content.append("This project currently uses the following submodules as editable installs:")
  for module_name in selected_modules:
    local_path = os.path.relpath(SUBMODULES[module_name], start=target_dir)
    file_content.append(f"\t- {module_name}: installed from local path: {local_path}")
    file_content.append(f"\t\tUninstall with: `uv pip uninstall {module_name}` # from the project root")
  file_content.append("")
  file_content.append("To make this project standalone, do the following:")
  file_content.append("\t1. Uninstall each local editable install using the commands mentioned above.")
  file_content.append("\t2. Add the following entries to your [project.dependencies] section in pyproject.toml:")
  for module_name in selected_modules:
    repo_html  = GITHUB_REPOS[module_name]
    file_content.append(f"\t\t- `{repo_html}`")
  file_content.append("")
  file_content.append("Note: Run the uninstall commands from the project root so that uv uses the correct environment.")
  file_content.append("")
  file_path.write_text("\n".join(file_content))
  print(f"Wrote dependency notice to: {file_path}")

def main():
  ## parse user inputs
  user_args = parse_args()
  selected_modules = [
    module_name
    for module_name in SUBMODULES
    if getattr(user_args, module_name)
  ]
  if not sorted(selected_modules):
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
  ## make sure there is no self-linking
  for module_name in selected_modules:
    source_dir = SUBMODULES[module_name].resolve()
    if source_dir == target_dir:
      print(f"Error: Cannot link module `{module_name}` into itself (`target_dir == submodule`)")
      sys.exit(1)
  ## link all requested modules
  for module_name in selected_modules:
    link_editable(target_dir, module_name, dry_run)
  ## write a notice to undo linking and update pyproject to reflect dependency on submodules
  if not dry_run:
    write_dependency_notice(target_dir, selected_modules)

if __name__ == "__main__":
  main()

## .