## { SCRIPT

##
## === DEPENDENCIES
##

## stdlib
import argparse
import collections.abc
import dataclasses
import json
import sys
import tomllib
import typing

from pathlib import Path

## third-party
from jormi.ww_io import manage_log, manage_shell

##
## === GLOBAL PARAMS
##

SCRIPT_DIR = Path(__file__).resolve().parent
SINDRI_DIR = SCRIPT_DIR.parent.parent

SINDRI_PACKAGES: dict[str, Path] = {
    "jormi": SINDRI_DIR / "submodules/jormi",
    "bifrost": SINDRI_DIR / "submodules/bifrost",
    "vegtamr": SINDRI_DIR / "submodules/vegtamr",
    "quokka": SINDRI_DIR / "submodules/ww-quokka-sims",
    "flash": SINDRI_DIR / "submodules/ww-flash-sims",
    "arepo": SINDRI_DIR / "submodules/ww-arepo-sims",
}

##
## === TYPE ALIASES
##

AliasName = str
PackageName = str

##
## === DATA MODELS
##


@dataclasses.dataclass
class PackageStatus:
    is_valid: bool
    package_alias: AliasName
    package_path: Path
    package_name: PackageName | None
    reason: str | None
    is_installed: bool = False


@dataclasses.dataclass
class OutcomeSummary:
    install_self: bool | None = None
    uninstall_self: bool | None = None
    packages_installed: list[tuple[AliasName, bool]] = dataclasses.field(default_factory=list)
    packages_uninstalled: list[tuple[AliasName, bool]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class CommandOutcome:
    succeeded: bool
    output: str | None


##
## === FORMATTING HELPERS
##


def format_package_label(
    package_status: PackageStatus,
) -> str:
    arrow = manage_log.Symbols.RIGHT_ARROW.value
    if package_status.package_name and (package_status.package_name != package_status.package_alias):
        alias_mapping = f"{package_status.package_alias} {arrow} {package_status.package_name}"
    else:
        alias_mapping = package_status.package_alias
    if package_status.is_valid:
        return alias_mapping
    return f"{alias_mapping}[{package_status.reason}]"


def format_success_and_failure(
    *,
    results: list[tuple[AliasName, bool]],
    sindri_packages: dict[AliasName, PackageStatus],
) -> tuple[list[str], list[str]]:
    succeeded: list[str] = []
    failed: list[str] = []
    for package_alias, action_status in results:
        package_label = format_package_label(sindri_packages[package_alias])
        (succeeded if action_status else failed).append(package_label)
    return succeeded, failed


def format_optional_outcome(
    command_outcome: bool | None,
) -> str:
    if command_outcome is None:
        return manage_log.Symbols.EM_DASH.value
    return "succeeded" if command_outcome else "failed"


def format_list(
    items: collections.abc.Iterable[str | None],
) -> str:
    cleaned_items = [item for item in items if item]
    if cleaned_items:
        return ", ".join(cleaned_items)
    return manage_log.Symbols.EM_DASH.value


def format_path(
    path: Path,
) -> str:
    hooked_arrow = manage_log.Symbols.HOOKED_ARROW.value
    return f"\n\t{hooked_arrow} {path}"


##
## === PYPROJECT / SHELL HELPERS
##


def run_command(
    command: str,
    *,
    working_directory: Path | None = None,
    timeout_seconds: int = 90,
    capture_output: bool = False,
    use_shell: bool = False,
    message: str | None = None,
) -> CommandOutcome:
    try:
        if message:
            manage_log.log_task(message, show_time=True)
        result = manage_shell.execute_shell_command(
            command,
            working_directory=working_directory,
            timeout_seconds=timeout_seconds,
            use_shell=use_shell,
            capture_output=capture_output,
            raise_on_error=False,
        )
        return CommandOutcome(
            succeeded=result.succeeded,
            output=result.stdout,
        )
    except Exception as exception:
        manage_log.log_outcome(
            f"Command failed: {command}\n{exception}",
            outcome=manage_log.ActionOutcome.FAILURE,
        )
        return CommandOutcome(
            succeeded=False,
            output=None,
        )


##
## === PACKAGE VERIFICATION
##


def read_package_name(
    target_dir: Path,
) -> str:
    pyproject_path = target_dir / "pyproject.toml"
    with pyproject_path.open("rb") as fp:
        pyproject = tomllib.load(fp)
    package_name = pyproject.get("project", {}).get("name")
    if not package_name or not isinstance(package_name, str):
        raise ValueError(f"Could not determine package name from: {format_path(pyproject_path)}")
    return package_name.lower()


def get_package_status(
    package_alias: AliasName,
) -> PackageStatus:
    package_path = SINDRI_PACKAGES[package_alias].resolve()
    if not package_path.exists():
        return PackageStatus(
            package_alias=package_alias,
            package_path=package_path,
            package_name=None,
            is_valid=False,
            reason="missing-path",
        )
    pyproject_path = package_path / "pyproject.toml"
    if not pyproject_path.exists():
        return PackageStatus(
            package_alias=package_alias,
            package_path=package_path,
            package_name=None,
            is_valid=False,
            reason="missing-pyproject",
        )
    try:
        package_name = read_package_name(package_path)
        return PackageStatus(
            package_alias=package_alias,
            package_path=package_path,
            package_name=package_name,
            is_valid=True,
            reason=None,
        )
    except Exception:
        return PackageStatus(
            package_alias=package_alias,
            package_path=package_path,
            package_name=None,
            is_valid=False,
            reason="missing-package-name",
        )


##
## === ENV INSPECTION (uv)
##


def update_installed_status(
    *,
    sindri_packages: dict[AliasName, PackageStatus],
) -> None:
    command_outcome = run_command("uv pip list --format=json", capture_output=True)
    packages_installed: set[str] = set()
    if command_outcome.succeeded and command_outcome.output:
        try:
            entries = json.loads(command_outcome.output)
            packages_installed = {
                str(
                    entry.get(
                        "name",
                        "",
                    ),
                ).lower()
                for entry in entries
                if isinstance(entry, dict)
            }
        except Exception:
            packages_installed = set()
    for package_status in sindri_packages.values():
        package_status.is_installed = bool(
            package_status.is_valid and package_status.package_name
            and package_status.package_name.lower() in packages_installed,
        )


##
## === ENVIRONMENT CHECKS
##


def ensure_package_root(
    target_dir: Path,
) -> None:
    venv_path = target_dir / ".venv"
    if not venv_path.exists() or not venv_path.is_dir():
        raise FileNotFoundError(
            f"No virtual-environment directory was found under: {format_path(venv_path)}\n"
            "Create with: `uv venv`.",
        )


##
## === RENDERING
##


def print_sindri_status(
    *,
    sindri_packages: dict[AliasName, PackageStatus],
) -> None:
    details: list[tuple[str, str, str]] = []
    for package_alias in sorted(sindri_packages):
        package_status = sindri_packages[package_alias]
        package_label = format_package_label(package_status)
        package_path = f"{manage_log.Symbols.HOOKED_ARROW.value} path: {package_status.package_path}"
        if not package_status.is_valid:
            package_state = f"broken[{package_status.reason}]"
        else:
            package_state = "installed" if package_status.is_installed else "not installed"
        details.append((package_label, package_state, package_path))
    notes: dict[str, str] = {
        package_label: f"{package_state}\n{4 * ' '}{package_path}"
        for (package_label, package_state, package_path) in details
    }
    num_installed = sum(
        1 for package_state in sindri_packages.values()
        if package_state.is_valid and package_state.is_installed
    )
    num_broken = sum(1 for package_state in sindri_packages.values() if not package_state.is_valid)
    num_missing = max(len(sindri_packages) - num_installed - num_broken, 0)
    notes["summary"] = f"installed={num_installed}, not installed={num_missing}, broken={num_broken}"
    manage_log.log_context(
        title="Sindri Packages",
        message="Sindri packages and their install state in this project.",
        notes=notes,
    )


##
## === CORE ACTIONS
##


def install_self(
    *,
    target_dir: Path,
) -> bool:
    package_name = read_package_name(target_dir)
    command = "uv pip install -e ."
    notes = {
        "package-name": package_name,
        "package-path": str(target_dir),
    }
    command_outcome = run_command(
        command,
        message=f"Installing `{package_name}` package",
        working_directory=target_dir,
        capture_output=False,
    )
    manage_log.log_empty_lines()
    message = f"Command: {command}"
    succeeded = command_outcome.succeeded
    manage_log.log_action(
        title=f"Install `{package_name}`",
        outcome=manage_log.ActionOutcome.SUCCESS if succeeded else manage_log.ActionOutcome.FAILURE,
        message=message,
        notes=notes,
    )
    return succeeded


def uninstall_self(
    *,
    target_dir: Path,
) -> bool:
    package_name = read_package_name(target_dir)
    command = f"uv pip uninstall {package_name}"
    command_outcome = run_command(
        command,
        message=f"Uninstalling `{package_name}` package",
        working_directory=target_dir,
        capture_output=False,
    )
    manage_log.log_empty_lines()
    message = f"Command: {command}"
    succeeded = command_outcome.succeeded
    manage_log.log_action(
        title=f"Uninstall `{package_name}`",
        outcome=manage_log.ActionOutcome.SUCCESS if succeeded else manage_log.ActionOutcome.FAILURE,
        message=message,
        notes={
            "package-name": package_name,
            "package-path": str(target_dir),
        },
    )
    return succeeded


def install_package(
    *,
    target_dir: Path,
    package_alias: AliasName,
    sindri_packages: dict[AliasName, PackageStatus],
) -> bool:
    package_status = sindri_packages[package_alias]
    notes = {
        "package-alias": package_alias,
        "package-name": package_status.package_name,
        "package-path": str(package_status.package_path),
        "target-package": str(target_dir),
    }
    command = f'uv pip install -e "{package_status.package_path}"'
    if not (package_status.is_valid and package_status.package_name):
        notes["reason"] = str(package_status.reason)
        message = f"Failed. Broken package: {package_status.reason}."
        succeeded = False
    elif not package_status.package_path.exists():
        message = "Failed. Package path does not exist."
        succeeded = False
    elif package_status.package_path.resolve() == target_dir.resolve():
        message = "Failed. Refused to install package into itself; pass the `--self-install` flag instead."
        succeeded = False
    else:
        command_outcome = run_command(
            command,
            working_directory=target_dir,
            capture_output=False,
            message=f"Installing `{package_status.package_name}` package",
        )
        manage_log.log_empty_lines()
        message = f"Command: {command}"
        succeeded = command_outcome.succeeded
    manage_log.log_action(
        title=f"Install `{format_package_label(package_status)}`",
        outcome=manage_log.ActionOutcome.SUCCESS if succeeded else manage_log.ActionOutcome.FAILURE,
        message=message,
        notes=notes,
    )
    return succeeded


def uninstall_package(
    *,
    target_dir: Path,
    package_alias: AliasName,
    sindri_packages: dict[AliasName, PackageStatus],
) -> bool:
    package_status = sindri_packages[package_alias]
    notes = {
        "package-alias": package_alias,
        "package-name": package_status.package_name,
        "package-path": str(package_status.package_path),
        "target-package": str(target_dir),
    }
    succeeded: bool
    if not (package_status.is_valid and package_status.package_name):
        notes["reason"] = str(package_status.reason)
        message = "Failed. Broken package (cannot resolve package name)."
        succeeded = False
    else:
        command = f"uv pip uninstall {package_status.package_name}"
        command_outcome = run_command(
            command,
            working_directory=target_dir,
            capture_output=False,
            message=f"Uninstalling `{package_status.package_name}` package",
        )
        manage_log.log_empty_lines()
        message = f"Command: {command}"
        succeeded = command_outcome.succeeded
    manage_log.log_action(
        title=f"Uninstall `{format_package_label(package_status)}`",
        outcome=manage_log.ActionOutcome.SUCCESS if succeeded else manage_log.ActionOutcome.FAILURE,
        message=message,
        notes=notes,
    )
    return succeeded


##
## === CLI
##


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage sindri packages.")
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Target package directory (must contain pyproject.toml and .venv)",
    )
    parser.add_argument(
        "--self-install",
        action="store_true",
        help="Editable install of the project package",
    )
    parser.add_argument(
        "--self-uninstall",
        action="store_true",
        help="Uninstall the project package",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check sindri package status",
    )
    for package_alias in sorted(SINDRI_PACKAGES):
        package_path = SINDRI_PACKAGES[package_alias]
        parser.add_argument(
            f"--{package_alias}",
            action="store_true",
            help=f"Install package: {package_path}",
        )
        parser.add_argument(
            f"--no-{package_alias}",
            action="store_true",
            help=f"Uninstall package: {package_path}",
        )
    return parser.parse_args()


##
## === WORKFLOW
##


@typing.final
class LinkPackages:

    def __init__(
        self,
        user_args: argparse.Namespace,
    ) -> None:
        self.user_args = user_args
        self.target_dir: Path | None = None
        self.aliases_to_install: list[AliasName] = []
        self.aliases_to_uninstall: list[AliasName] = []
        self.do_self_install: bool = False
        self.do_self_uninstall: bool = False
        self.show_sindri_status: bool = False
        self.sindri_packages: dict[AliasName, PackageStatus] = {}
        self.outcome_summary = OutcomeSummary()

    def _validate_package_root(
        self,
    ) -> None:
        target_dir = self.user_args.target_dir.resolve()
        if not target_dir.exists():
            raise FileNotFoundError(f"Target package directory does not exist: {format_path(target_dir)}")
        pyproject_path = target_dir / "pyproject.toml"
        if not pyproject_path.exists():
            manage_log.log_outcome(
                f"No pyproject.toml found under: {format_path(target_dir)}",
                outcome=manage_log.ActionOutcome.FAILURE,
            )
            sys.exit(1)
        try:
            ensure_package_root(target_dir)
        except Exception as exception:
            manage_log.log_outcome(str(exception), outcome=manage_log.ActionOutcome.FAILURE)
            sys.exit(1)
        self.target_dir = target_dir

    def _collect_actions_from_args(
        self,
    ) -> None:
        self.do_self_install = bool(self.user_args.self_install)
        self.do_self_uninstall = bool(self.user_args.self_uninstall)
        self.aliases_to_install = [
            package_alias for package_alias in sorted(SINDRI_PACKAGES)
            if getattr(self.user_args, package_alias)
        ]
        self.aliases_to_uninstall = [
            package_alias for package_alias in sorted(SINDRI_PACKAGES)
            if getattr(self.user_args, f"no_{package_alias}")
        ]
        self.show_sindri_status = bool(self.user_args.status)

    def _render_and_confirm_plan(
        self,
    ) -> None:
        labels_broken_requests = [
            format_package_label(self.sindri_packages[package_alias])
            for package_alias in (self.aliases_to_install + self.aliases_to_uninstall)
            if not self.sindri_packages[package_alias].is_valid
        ]
        labels_requested_installs = [
            format_package_label(self.sindri_packages[package_alias])
            for package_alias in self.aliases_to_install
            if self.sindri_packages[package_alias].is_valid
        ]
        labels_requested_uninstalls = [
            format_package_label(self.sindri_packages[package_alias])
            for package_alias in self.aliases_to_uninstall
            if self.sindri_packages[package_alias].is_valid
        ]
        labels_installed_packages = [
            format_package_label(package_status)
            for package_status in self.sindri_packages.values()
            if package_status.is_installed
        ]
        labels_packages_not_installed = [
            format_package_label(package_status)
            for package_status in self.sindri_packages.values()
            if not package_status.is_installed
        ]
        notes: dict[str, typing.Any] = {
            "target project": str(self.target_dir),
            "self-install": self.do_self_install,
            "self-uninstall": self.do_self_uninstall,
            "requested installs": format_list(labels_requested_installs),
            "requested uninstalls": format_list(labels_requested_uninstalls),
            "requested broken packages": format_list(labels_broken_requests),
            "installed packages": format_list(labels_installed_packages),
            "packages not installed": format_list(labels_packages_not_installed),
            "show sindri status": self.show_sindri_status,
        }
        manage_log.log_context(
            title="Planned Actions",
            notes=notes,
            message="Review the items above.",
        )
        user_response = input("Proceed? [y/N]: ").strip().lower()
        if user_response not in ("y", "yes"):
            manage_log.log_outcome("Aborted by user.", outcome=manage_log.ActionOutcome.SKIPPED)
            sys.exit(1)
        manage_log.log_empty_lines()

    def parse_and_verify_args(
        self,
    ) -> None:
        self._validate_package_root()
        self.sindri_packages = {
            package_alias: get_package_status(package_alias)
            for package_alias in SINDRI_PACKAGES
        }
        update_installed_status(sindri_packages=self.sindri_packages)
        self._collect_actions_from_args()
        self._render_and_confirm_plan()

    def apply_requested_actions(
        self,
    ) -> None:
        assert self.target_dir is not None
        for package_alias in self.aliases_to_uninstall:
            succeeded = uninstall_package(
                target_dir=self.target_dir,
                package_alias=package_alias,
                sindri_packages=self.sindri_packages,
            )
            self.outcome_summary.packages_uninstalled.append((package_alias, succeeded))
        for package_alias in self.aliases_to_install:
            succeeded = install_package(
                target_dir=self.target_dir,
                package_alias=package_alias,
                sindri_packages=self.sindri_packages,
            )
            self.outcome_summary.packages_installed.append((package_alias, succeeded))
        if self.do_self_uninstall:
            self.outcome_summary.uninstall_self = uninstall_self(
                target_dir=self.target_dir,
            )
        if self.do_self_install:
            self.outcome_summary.install_self = install_self(
                target_dir=self.target_dir,
            )
        update_installed_status(sindri_packages=self.sindri_packages)
        if self.show_sindri_status:
            print_sindri_status(sindri_packages=self.sindri_packages)

    def summarise_and_exit(
        self,
    ) -> None:
        successful_installs, failed_installs = format_success_and_failure(
            results=self.outcome_summary.packages_installed,
            sindri_packages=self.sindri_packages,
        )
        successful_uninstalls, failed_uninstalls = format_success_and_failure(
            results=self.outcome_summary.packages_uninstalled,
            sindri_packages=self.sindri_packages,
        )
        manage_log.log_summary(
            title="Final Summary",
            message="Finished.",
            notes={
                "self-install": format_optional_outcome(self.outcome_summary.install_self),
                "self-uninstall": format_optional_outcome(self.outcome_summary.uninstall_self),
                "Successfully installed": format_list(successful_installs),
                "Successfully uninstalled": format_list(successful_uninstalls),
                "Failed to install": format_list(failed_installs),
                "Failed to uninstall": format_list(failed_uninstalls),
            },
        )
        summary_status: list[bool] = []
        if self.outcome_summary.install_self is not None:
            summary_status.append(self.outcome_summary.install_self)
        if self.outcome_summary.uninstall_self is not None:
            summary_status.append(self.outcome_summary.uninstall_self)
        summary_status.extend(succeeded for (_, succeeded) in self.outcome_summary.packages_uninstalled)
        summary_status.extend(succeeded for (_, succeeded) in self.outcome_summary.packages_installed)
        sys.exit(0 if all(summary_status) else 1)

    def run(
        self,
    ) -> None:
        self.parse_and_verify_args()
        self.apply_requested_actions()
        self.summarise_and_exit()


##
## === MAIN ROUTINE
##


def main() -> None:
    user_args = parse_args()
    LinkPackages(user_args).run()


##
## === ENTRY POINT
##

if __name__ == "__main__":
    main()

## } SCRIPT
