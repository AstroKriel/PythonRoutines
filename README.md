# Sindri

Sindri is Asgard's Python dev layer. It's the home of Asgard's shared Python packages (see [Project layout](#project-layout)), and provides two command line tools to help with development. You can install and manage these tools using the convenient scripts in [Setup](#setup), which make these tools available system-wide, independently of any project's virtual environment; pass `-h` to either tool for usage details.

`sindri_packages.py` manages which Asgard submodule packages are installed into a given project's `.venv`. It's intended for active development alongside packages that are not yet pinned as formal dependencies. It takes a `target_dir` (the project root), flags for each package (`--jormi`, `--quokka`, etc.) with `--no-<package>` variants to uninstall, `--self-install`/`--self-uninstall` for the target project's own package, and `--status` to show the current install state of all packages. Once a dependency is settled, it should be declared properly in `pyproject.toml` and the local install removed.

`format_python_files.py` standardises the formatting of Python file content (indentation, spacing, line length, etc.) based on the rules defined in `.style.yapf`. It optionally takes `targets` (files or directories); if none are given, it recursively formats from the current working directory.

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
