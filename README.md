# sindri

`sindri` is [Asgard](https://github.com/AstroKriel/Asgard)'s Python dev layer. It's the home of my Python packages (see [Project layout](#project-layout)), and provides two command line tools to help with development. You can install and manage these tools using the convenient scripts in [Setup](#setup), which make these tools available system-wide, independent of any project's virtual environment; pass `-h` to either tool for usage details.

`sindri_packages.py` manages which `sindri/submodules/` packages are installed into a given Python project's `.venv`. This is intended when the repository is under active development alongside the packages that are not yet pinned as formal dependencies. This script takes a `target_dir` (the project root), and flags for each package (`--jormi`, `--quokka`, etc.) with `--no-<package>` variants to uninstall, and `--self-install`/`--self-uninstall` for the target project's own package; `--status` shows the current installed state of all packages in the current repo. Once a dependency is settled, it should be declared properly in `pyproject.toml` and the local install should be removed.

`format_python_files.py` standardises the formatting of Python file content (indentation, spacing, line length, etc.) based on the rules defined in `.style.yapf`. It also optionally takes `targets` (files or directories); if none are given, then it recursively formats all Python files under the current working directory.

## Setup

Convenience shell scripts are provided for install, update, and removal, and should be run from the `sindri` root (`Asgard/sindri/`):

```bash
./install_sindri_tools.sh    # first-time install
./update_sindri_tools.sh     # update tools and integrate changes made
./uninstall_sindri_tools.sh  # remove tools
```

After installing, run `hash -r` if commands are not immediately found in your shell.

`sindri` depends on `jormi` (for logging and shell utilities), and uses `jormi` installed as a non-editable path dependency. After significant `jormi` updates, run `./update_sindri_tools.sh` to reinstall.

## Project layout

```
sindri/
├── tools/
│   └── sindri_cli/            # source for both command line tools
├── submodules/
│   ├── jormi/                 # utility library (logging, shell, numerics)
│   ├── bifrost/               # data pipeline utilities
│   ├── vegtamr/               # visualisation utilities
│   ├── ww-quokka-sims/        # QUOKKA simulation interface
│   ├── ww-flash-sims/         # FLASH simulation interface
│   └── ww-arepo-sims/         # AREPO simulation interface
├── pyproject.toml             # package definition and tooling config
├── install_sindri_tools.sh
├── update_sindri_tools.sh
└── uninstall_sindri_tools.sh
```
