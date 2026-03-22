# Sindri

Sindri is Asgard's Python dev layer, installed as a `uv tool` (its own isolated environment, with commands available system-wide, independently of any project's virtual environment). It provides two command line tools:

`sindri_packages.py` manages which Asgard submodule packages are installed into a given project's `.venv`. It is intended for active development against packages like `jormi` or `bifrost` that are not yet pinned as formal dependencies. It takes a `target_dir` (the project root) and flags for each package (`--jormi`, `--bifrost`, etc.), with `--no-<package>` variants to uninstall. `--self-install` and `--self-uninstall` handle the target project's own package, and `--status` shows the current install state of all packages. Note: local editable installs wired up this way are a development convenience. Once a package dependency is settled, it should be declared properly in the project's dependency manager (e.g. `pyproject.toml` via uv) and the local install removed.

`format_python_files.py` runs trailing-comma cleanup followed by YAPF formatting across a set of Python files, applying consistent style rules defined in `.style.yapf`. It takes zero or more `targets` (files or directories); if none are given, it formats from the current working directory.

## Setup

Convenience shell scripts are provided for install, update, and removal, and should be run from the Sindri root (`Asgard/sindri/`):

```bash
./install_sindri_tools.sh    # first-time install
./update_sindri_tools.sh     # update tools and integrate changes made
./uninstall_sindri_tools.sh  # remove tools
```

After installing, run `hash -r` if commands are not immediately found in your shell.

Sindri depends on `jormi` (logging and shell utilities), installed as a non-editable path dependency. After significant jormi updates, run `./update_sindri_tools.sh` to reinstall.

## Project layout

```
sindri/
├── tools/
│   └── sindri_cli/            # source for both command line tools
├── submodules/
│   ├── jormi/                 # utility library (logging, shell, numerics)
│   ├── bifrost/               # data pipeline utilities
│   ├── vegtamr/               # visualisation utilities
│   ├── ww_quokka_sims/        # Quokka simulation interface
│   ├── ww_flash_sims/         # FLASH simulation interface
│   └── ww_arepo_sims/         # Arepo simulation interface
├── pyproject.toml             # package definition and tooling config
├── install_sindri_tools.sh
├── update_sindri_tools.sh
└── uninstall_sindri_tools.sh
```
