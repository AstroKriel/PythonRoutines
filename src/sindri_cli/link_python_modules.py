## { SCRIPT


import sys
import argparse
import subprocess
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
SINDRI_DIR = _SCRIPT_DIR.parent.parent

SUBMODULES = {
  "arepo"   : SINDRI_DIR / "submodules/ww_arepo_sims",
  "flash"   : SINDRI_DIR / "submodules/ww_flash_sims",
  "quokka"  : SINDRI_DIR / "submodules/ww_quokka_sims",
  "bifrost" : SINDRI_DIR / "submodules/bifrost",
  "jormi"   : SINDRI_DIR / "submodules/jormi",
  "vegtamr" : SINDRI_DIR / "submodules/vegtamr",
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
  parser = argparse.ArgumentParser(description="Link submodules into and/or install a project-env managed by uv.")
  parser.add_argument("target_dir", type=Path, help="Target project directory (must contain a pyproject.toml)")
  parser.add_argument("--self", action="store_true", help="Install the project: `uv pip install -e .`")
  for module_alias in sorted(SUBMODULES):
    module_name = SUBMODULES[module_alias].name
    parser.add_argument(f"--{module_alias}", action="store_true", help=f"Link python submodule `{module_name}`")
  parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
  return parser.parse_args()

def run_command(
    cmd : list[str],
    cwd : Path | None = None
  ) -> bool:
  if cwd:
    cwd = str(cwd)
  try:
    subprocess.run(cmd, cwd=cwd, check=True)
    return True
  except subprocess.CalledProcessError as e:
    cmd_str = " ".join(cmd)
    print(f"Error: command failed: {cmd_str}\n{e}")
    return False

def install_project(
    project_dir : Path,
    dry_run     : bool
  ) -> bool:
  if dry_run:
    print(f"[dry-run] Would run in {project_dir}: uv pip install -e .")
    return True
  print(f"Installing the project in editable mode: {project_dir}")
  return run_command(["uv", "pip", "install", "-e", "."], cwd=project_dir)

def link_dependency(
    target_dir   : Path,
    module_alias : str,
    dry_run      : bool = False
  ) -> bool:
  ## confirm the requested module exists
  module_path = SUBMODULES[module_alias]
  module_name = module_path.name
  if not module_path or not module_path.exists():
    print(f"Error: `{module_name}` could not be found under: {module_path}")
    return False
  ## link (editable install) the module
  if dry_run:
    print(f"[dry-run] Would link `{module_name}` located under: {module_path}")
    return True
  else:
    print(f"Linking `{module_name}` located under: {module_path}")
    return run_command(["uv", "pip", "install", "-e", str(module_path)], cwd=target_dir)

def write_dependency_notice(
    target_dir : Path,
    linked_module_aliases : list[str]
  ):
  if not linked_module_aliases: return
  file_path = target_dir / "DEPENDENCY_NOTICE.txt"
  file_content = []
  file_content.append("This project currently uses the following submodules as editable installs:")
  for module_alias in linked_module_aliases:
    module_path = SUBMODULES[module_alias]
    module_name = module_path.name
    file_content.append(f"\t- {module_name}: installed from local path: {module_path}")
    file_content.append(f"\t\tUninstall with: `uv pip uninstall {module_name}` # from the project root")
  file_content.append("")
  file_content.append("To make this project standalone, do the following:")
  file_content.append("\t1. Uninstall each local editable install using the commands mentioned above.")
  file_content.append("\t2. Add the following entries to your [project.dependencies] section in pyproject.toml:")
  for module_alias in linked_module_aliases:
    repo_html = GITHUB_REPOS[module_alias]
    file_content.append(f"\t\t- `{repo_html}`")
  file_content.append("")
  file_content.append("Note: Run the uninstall commands from the project root so that uv uses the correct environment.")
  file_content.append("")
  file_path.write_text("\n".join(file_content))
  print(f"Wrote dependency notice to: {file_path}")

def main():
  ## parse user inputs
  user_args = parse_args()
  target_dir = user_args.target_dir.resolve()
  dry_run = user_args.dry_run
  install_self = user_args.self
  selected_module_aliases = [
    module_alias
    for module_alias in sorted(SUBMODULES)
    if getattr(user_args, module_alias)
  ]
  if not install_self and not selected_module_aliases:
    print("No actions were provided. Use --self to install the current project, or link submodules via:")
    print("  " + " ".join(f"--{module_alias}" for module_alias in SUBMODULES))
    sys.exit(1)
  ## confirm target project directory
  if not target_dir.exists():
    raise FileNotFoundError(f"Target project directory does not exist: {target_dir}")
  print(f"Target project directory: {target_dir}")
  user_response = input("Is this correct? [y/N]: ").strip().lower()
  if user_response not in ("y", "yes"):
    print("Aborting.")
    sys.exit(1)
  ## make sure the project directory has a pyproject.toml file
  pyproject_path = target_dir / "pyproject.toml"
  if not pyproject_path.exists():
    print(f"Error: no pyproject.toml found in {target_dir}")
    sys.exit(1)
  ## make sure there is no self-linking
  for module_alias in selected_module_aliases:
    source_dir = SUBMODULES[module_alias].resolve()
    if source_dir == target_dir:
      print(f"Aborting. Refusing to link module `{module_alias}` into itself.")
      sys.exit(1)
  if user_args.self:
    if not install_project(target_dir, dry_run):
      print("Warning: editable install of the project failed.")
  ## link requested modules
  linked_module_aliases = []
  for module_alias in selected_module_aliases:
    if link_dependency(target_dir, module_alias, dry_run):
      linked_module_aliases.append(module_alias)
  ## write a notice to undo linking and update pyproject to reflect dependency on submodules
  if not dry_run and linked_module_aliases:
    write_dependency_notice(target_dir, linked_module_aliases)

if __name__ == "__main__":
  main()

## } SCRIPT