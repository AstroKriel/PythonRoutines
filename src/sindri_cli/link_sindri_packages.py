## { SCRIPT

##
## === DEPENDENCIES ===
##

import sys
import json
import tomllib
import argparse
from typing import Any
from pathlib import Path
from dataclasses import dataclass, field
from jormi.ww_io import shell_manager, log_manager

##
## === GLOBAL PARAMS ===
##

_SCRIPT_DIR = Path(__file__).resolve().parent
SINDRI_DIR = _SCRIPT_DIR.parent.parent

SINDRI_PACKAGES: dict[str, Path] = {
    "jormi": SINDRI_DIR / "submodules/jormi",
    "bifrost": SINDRI_DIR / "submodules/bifrost",
    "vegtamr": SINDRI_DIR / "submodules/vegtamr",
    "quokka": SINDRI_DIR / "submodules/ww_quokka_sims",
    "flash": SINDRI_DIR / "submodules/ww_flash_sims",
    "arepo": SINDRI_DIR / "submodules/ww_arepo_sims",
}

##
## === TYPE ALIASES ===
##

AliasName = str
PackageName = str

##
## === DATA MODELS ===
##


@dataclass
class PlannedActions:
    install_names: list[PackageName] = field(default_factory=list)
    uninstall_names: list[PackageName] = field(default_factory=list)


@dataclass
class OutcomeSummary:
    install_self: bool | None = None
    uninstall_self: bool | None = None
    uninstalled_packages: list[tuple[AliasName, bool | None]] = field(default_factory=list)
    installed_packages: list[tuple[AliasName, bool | None]] = field(default_factory=list)
    broken_aliases: list[tuple[AliasName, str]] = field(default_factory=list)


@dataclass(frozen=True)
class PackageStatus:
    is_valid: bool
    package_alias: AliasName
    package_path: Path
    package_name: PackageName | None
    reason: str | None


@dataclass(frozen=True)
class CommandOutcome:
    success: bool
    output: str | None


##
## === FORMATTING HELPERS ===
##


def format_package_alias(
    package_alias: AliasName,
    package_name: PackageName | None = None,
) -> str:
    if (package_name is None) or (package_alias == package_name):
        return package_alias
    else:
        return f"{package_alias} {log_manager.Symbols.RIGHT_ARROW.value} {package_name}"


def format_optional_outcome(
    outcome: bool | None,
) -> str:
    if outcome is None:
        return log_manager.Symbols.EM_DASH.value
    elif outcome:
        return "succeeded"
    else:
        return "failed"


def format_list(items: list[str]) -> str:
    if items:
        return ", ".join(items)
    else:
        return log_manager.Symbols.EM_DASH.value


def split_success_and_failure(
    *,
    results: list[tuple[AliasName, bool | None]],
    sindri_packages: dict[AliasName, PackageStatus],
) -> tuple[list[PackageName], list[PackageName]]:
    succeeded: list[PackageName] = []
    failed: list[PackageName] = []
    for package_alias, success in results:
        if success is None: continue
        status = sindri_packages[package_alias]
        package_name = status.package_name or package_alias
        if success:
            succeeded.append(package_name)
        else:
            reason = status.reason if not status.is_valid else None
            failed.append(package_name if not reason else f"{package_name}[{reason}]")
    return succeeded, failed


##
## === PYPROJECT / SHELL HELPERS ===
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
            log_manager.log_task(message, show_time=True)
        result = shell_manager.execute_shell_command(
            command,
            working_directory=working_directory,
            timeout_seconds=timeout_seconds,
            use_shell=use_shell,
            capture_output=capture_output,
        )
        return CommandOutcome(
            success=result.succeeded,
            output=result.stdout if capture_output else None,
        )
    except Exception as exception:
        log_manager.log_outcome(
            f"Command failed: {command}\n{exception}",
            outcome=log_manager.ActionOutcome.FAILURE,
        )
        return CommandOutcome(
            success=False,
            output=None,
        )


##
## === PACKAGE VERIFICATION ===
##


def verify_sindri_package(
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


def read_package_name(
    target_dir: Path,
) -> str:
    pyproject_path = target_dir / "pyproject.toml"
    with pyproject_path.open("rb") as fp:
        pyproject = tomllib.load(fp)
    package_name = pyproject.get("project", {}).get("name")
    if not package_name or not isinstance(package_name, str):
        raise ValueError(f"Could not determine package name from: {pyproject_path}")
    return package_name.lower()


##
## === ENV INSPECTION (uv) ===
##


def get_installed_state(
    *,
    sindri_packages: dict[AliasName, PackageStatus],
) -> dict[AliasName, bool]:
    outcome = run_command("uv pip list --format=json", capture_output=True)
    installed_packages: set[str] = set()
    if outcome.success and outcome.output:
        try:
            entries = json.loads(outcome.output)
            installed_packages = {
                str(entry.get("name", "")).lower()
                for entry in entries
                if isinstance(entry, dict)
            }
        except Exception:
            installed_packages = set()
    state: dict[AliasName, bool] = {}
    for package_alias, status in sindri_packages.items():
        state[package_alias] = bool(
            status.is_valid and status.package_name
            and status.package_name.lower() in installed_packages,
        )
    return state


def format_installed_state(
    state: dict[AliasName, bool],
    *,
    sindri_packages: dict[AliasName, PackageStatus],
) -> tuple[str, str]:
    dash = log_manager.Symbols.EM_DASH.value
    installed_aliases = sorted([alias_name for (alias_name, success) in state.items() if success])
    missing_aliases = sorted([alias_name for (alias_name, success) in state.items() if not success])
    installed_labels = [
        format_package_alias(alias_name, sindri_packages[alias_name].package_name)
        for alias_name in installed_aliases
    ]
    missing_labels = [
        format_package_alias(alias_name, sindri_packages[alias_name].package_name)
        for alias_name in missing_aliases
    ]
    return (
        ", ".join(installed_labels) if installed_labels else dash,
        ", ".join(missing_labels) if missing_labels else dash,
    )


##
## === ENVIRONMENT CHECKS ===
##


def ensure_package_root(
    target_dir: Path,
) -> None:
    venv_path = target_dir / ".venv"
    if not venv_path.exists() or not venv_path.is_dir():
        raise FileNotFoundError(
            f"No virtual-environment directory found under: {venv_path}\n"
            "Create with: `uv venv`.",
        )


##
## === RENDERING ===
##


def print_sindri_status(
    *,
    sindri_packages: dict[AliasName, PackageStatus],
    sindri_installed_state: dict[AliasName, bool],
) -> None:
    rows: list[tuple[str, str, str]] = []
    for package_alias in sorted(sindri_packages):
        status = sindri_packages[package_alias]
        label = format_package_alias(package_alias, status.package_name)
        if not status.is_valid:
            state_text = f"broken[{status.reason}]"
            detail = f"{log_manager.Symbols.HOOKED_ARROW.value} path: {status.package_path}"
        else:
            is_installed = bool(sindri_installed_state.get(package_alias, False))
            state_text = "installed" if is_installed else "not installed"
            detail = f"{log_manager.Symbols.HOOKED_ARROW.value} path: {status.package_path}"
        rows.append((label, state_text, detail))
    notes: dict[str, str] = {
        label: f"{state}\n{4 * ' '}{detail}"
        for (label, state, detail) in rows
    }
    num_broken = sum(
        1 for package_alias in sindri_packages if not sindri_packages[package_alias].is_valid
    )
    num_valid = len(sindri_packages) - num_broken
    num_installed = sum(
        1 for package_alias in sindri_packages if sindri_packages[package_alias].is_valid
        and sindri_installed_state.get(package_alias, False)
    )
    num_missing = max(num_valid - num_installed, 0)
    notes["summary"
          ] = f"installed={num_installed}, not-installed={num_missing}, broken={num_broken}"
    log_manager.log_context(
        title="Sindri Packages",
        message="Sindri packages and their install state in this project.",
        notes=notes,
    )


##
## === CORE ACTIONS ===
##


def install_self(
    *,
    target_dir: Path,
    dry_run: bool,
) -> bool | None:
    package_name = read_package_name(target_dir)
    command = "uv pip install -e ."
    notes = {
        "package-name": package_name,
        "package-path": str(target_dir),
    }
    if dry_run:
        message = "[dry-run] Would run: uv pip install -e ."
        succeeded = None
    else:
        outcome = run_command(
            command,
            message=f"Installing `{package_name}` package",
            working_directory=target_dir,
            capture_output=False,
        )
        log_manager.log_empty_lines()
        message = f"Command: {command}"
        succeeded = outcome.success
    log_manager.log_action(
        title=f"Install `{package_name}`",
        succeeded=succeeded,
        message=message,
        notes=notes,
    )
    return succeeded


def uninstall_self(
    *,
    target_dir: Path,
    dry_run: bool,
) -> bool | None:
    package_name = read_package_name(target_dir)
    command = f"uv pip uninstall {package_name}"
    if dry_run:
        message = f"[dry-run] Would run: {command}"
        succeeded = None
    else:
        outcome = run_command(
            command,
            message=f"Uninstalling `{package_name}` package",
            working_directory=target_dir,
            capture_output=False,
        )
        log_manager.log_empty_lines()
        message = f"Command: {command}"
        succeeded = outcome.success
    log_manager.log_action(
        title=f"Uninstall `{package_name}`",
        succeeded=succeeded,
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
    dry_run: bool,
    sindri_packages: dict[AliasName, PackageStatus],
) -> bool | None:
    package_status = sindri_packages[package_alias]
    package_name = package_status.package_name
    package_path = package_status.package_path
    title = f"Install `{format_package_alias(package_alias, package_name)}`"
    notes = {
        "package-alias": package_alias,
        "package-name": package_name,
        "package-path": str(package_path),
        "target-package": str(target_dir),
    }
    command = f'uv pip install -e "{package_path}"'
    succeeded: bool | None
    if not (package_status.is_valid and package_name):
        notes["reason"] = str(package_status.reason)
        message = f"Failed. Broken package: {package_status.reason}."
        succeeded = False
    elif not package_path.exists():
        message = "Failed. Package path does not exist."
        succeeded = False
    elif package_path.resolve() == target_dir.resolve():
        message = "Failed. Refused to install package into itself."
        succeeded = False
    elif dry_run:
        message = f"[dry-run] Would run: {command}"
        succeeded = None
    else:
        outcome = run_command(
            command,
            working_directory=target_dir,
            capture_output=False,
            message=f"Installing `{package_name}` package",
        )
        log_manager.log_empty_lines()
        message = f"Command: {command}"
        succeeded = outcome.success
    log_manager.log_action(
        title=title,
        succeeded=succeeded,
        message=message,
        notes=notes,
    )
    return succeeded


def uninstall_package(
    *,
    target_dir: Path,
    package_alias: AliasName,
    dry_run: bool,
    sindri_packages: dict[AliasName, PackageStatus],
) -> bool | None:
    package_status = sindri_packages[package_alias]
    package_name = package_status.package_name
    notes = {
        "package-alias": package_alias,
        "package-name": package_name,
        "package-path": str(package_status.package_path),
        "target-package": str(target_dir),
    }
    succeeded: bool | None
    if not (package_status.is_valid and package_name):
        notes["reason"] = str(package_status.reason)
        message = "Failed. Broken package (cannot resolve package name)."
        succeeded = False
    elif dry_run:
        command = f"uv pip uninstall {package_name}"
        message = f"[dry-run] Would run: {command}"
        succeeded = None
    else:
        command = f"uv pip uninstall {package_name}"
        outcome = run_command(
            command,
            working_directory=target_dir,
            capture_output=False,
            message=f"Uninstalling `{package_name}` package",
        )
        log_manager.log_empty_lines()
        message = f"Command: {command}"
        succeeded = outcome.success
    log_manager.log_action(
        title=f"Uninstall `{format_package_alias(package_alias, package_name)}`",
        succeeded=succeeded,
        message=message,
        notes=notes,
    )
    return succeeded


##
## === CLI ===
##


def parse_args():
    parser = argparse.ArgumentParser(description="Install sindri packages.")
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Target package directory (must contain pyproject.toml and .venv)",
    )
    parser.add_argument(
        "--self-install",
        action="store_true",
        help="Editable install of the package itself",
    )
    parser.add_argument(
        "--self-uninstall",
        action="store_true",
        help="Uninstall the package editable install",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check sindri package status",
    )
    for package_alias in sorted(SINDRI_PACKAGES):
        package_pretty = SINDRI_PACKAGES[package_alias].name
        parser.add_argument(
            f"--{package_alias}",
            action="store_true",
            help=f"Install package `{package_pretty}`",
        )
        parser.add_argument(
            f"--no-{package_alias}",
            action="store_true",
            help=f"Uninstall package `{package_pretty}`",
        )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without executing",
    )
    return parser.parse_args()


##
## === WORKFLOW ===
##


class LinkPackages:

    def __init__(
        self,
        user_args,
    ):
        self.user_args = user_args
        self.target_dir: Path | None = None
        self.aliases_to_install: list[AliasName] = []
        self.aliases_to_uninstall: list[AliasName] = []
        self.do_self_install: bool = False
        self.do_self_uninstall: bool = False
        self.show_sindri_status: bool = False
        self.is_dry_run: bool = False
        self.sindri_packages: dict[AliasName, PackageStatus] = {}
        self.sindri_installed_state: dict[AliasName, bool] = {}
        self.action_plan = PlannedActions()
        self.outcome_summary = OutcomeSummary()

    def _validate_package_root(
        self,
    ) -> Path:
        target_dir = self.user_args.target_dir.resolve()
        if not target_dir.exists():
            raise FileNotFoundError(f"Target package directory does not exist: {target_dir}")
        pyproject_path = target_dir / "pyproject.toml"
        if not pyproject_path.exists():
            log_manager.log_outcome(
                f"No pyproject.toml found in {target_dir}",
                outcome=log_manager.ActionOutcome.FAILURE,
            )
            sys.exit(1)
        try:
            ensure_package_root(target_dir)
        except Exception as exception:
            log_manager.log_outcome(str(exception), outcome=log_manager.ActionOutcome.FAILURE)
            sys.exit(1)
        return target_dir

    def _collect_actions_from_args(
        self,
    ) -> None:
        self.aliases_to_install = [
            package_alias for package_alias in sorted(SINDRI_PACKAGES)
            if getattr(self.user_args, package_alias)
        ]
        self.aliases_to_uninstall = [
            package_alias for package_alias in sorted(SINDRI_PACKAGES)
            if getattr(self.user_args, f"no_{package_alias}")
        ]
        self.do_self_install = bool(self.user_args.self_install)
        self.do_self_uninstall = bool(self.user_args.self_uninstall)
        self.show_sindri_status = bool(self.user_args.status)
        self.is_dry_run = bool(self.user_args.dry_run)

    def _verify_and_prepare_plan(
        self,
    ) -> None:
        for package_alias in self.aliases_to_install:
            status = self.sindri_packages[package_alias]
            if not status.is_valid:
                self.outcome_summary.broken_aliases.append((package_alias, str(status.reason)))
        self.action_plan.install_names = [
            (self.sindri_packages[package_alias].package_name or package_alias)
            for package_alias in self.aliases_to_install
        ]
        self.action_plan.uninstall_names = [
            (self.sindri_packages[package_alias].package_name or package_alias)
            for package_alias in self.aliases_to_uninstall
        ]

    def _render_plan_and_confirm(
        self,
        *,
        target_dir: Path,
    ) -> None:
        installed_line, missing_line = format_installed_state(
            self.sindri_installed_state,
            sindri_packages=self.sindri_packages,
        )
        planned_installs = format_list(self.action_plan.install_names)
        planned_uninstalls = format_list(self.action_plan.uninstall_names)
        notes: dict[str, Any] = {
            "target-project": str(target_dir),
            "self-install": self.do_self_install,
            "self-uninstall": self.do_self_uninstall,
            "requested installs": planned_installs,
            "requested uninstalls": planned_uninstalls,
            "show sindri status": self.show_sindri_status,
            "dry-run": self.is_dry_run,
            "already installed packages": installed_line,
            "available packages": missing_line,
        }
        if self.outcome_summary.broken_aliases:
            broken_aliases = ", ".join(
                f"{format_package_alias(package_alias, self.sindri_packages[package_alias].package_name)}[{reason}]"
                for package_alias, reason in self.outcome_summary.broken_aliases
            )
            notes["requested broken packages"] = broken_aliases
        log_manager.log_context(
            title="Planned Actions",
            notes=notes,
            message="Review the items above.",
        )
        user_response = input("Proceed? [y/N]: ").strip().lower()
        if user_response not in ("y", "yes"):
            log_manager.log_outcome("Aborted by user.", outcome=log_manager.ActionOutcome.SKIPPED)
            sys.exit(1)
        log_manager.log_empty_lines()

    def parse_and_verify_args(
        self,
    ) -> None:
        target_dir = self._validate_package_root()
        self.sindri_packages = {
            package_alias: verify_sindri_package(package_alias)
            for package_alias in SINDRI_PACKAGES
        }
        self.sindri_installed_state = get_installed_state(sindri_packages=self.sindri_packages)
        self._collect_actions_from_args()
        self._verify_and_prepare_plan()
        self._render_plan_and_confirm(target_dir=target_dir)
        self.target_dir = target_dir

    def apply_requested_actions(
        self,
    ) -> None:
        assert self.target_dir is not None
        for package_alias in self.aliases_to_uninstall:
            successful = uninstall_package(
                target_dir=self.target_dir,
                package_alias=package_alias,
                dry_run=self.is_dry_run,
                sindri_packages=self.sindri_packages,
            )
            self.outcome_summary.uninstalled_packages.append((package_alias, successful))
        if self.do_self_uninstall:
            self.outcome_summary.uninstall_self = uninstall_self(
                target_dir=self.target_dir,
                dry_run=self.is_dry_run,
            )
        if self.do_self_install:
            self.outcome_summary.install_self = install_self(
                target_dir=self.target_dir,
                dry_run=self.is_dry_run,
            )
        for package_alias in self.aliases_to_install:
            successful = install_package(
                target_dir=self.target_dir,
                package_alias=package_alias,
                dry_run=self.is_dry_run,
                sindri_packages=self.sindri_packages,
            )
            self.outcome_summary.installed_packages.append((package_alias, successful))
        if self.show_sindri_status:
            print_sindri_status(
                sindri_packages=self.sindri_packages,
                sindri_installed_state=self.sindri_installed_state,
            )

    def summarise_and_exit(
        self,
    ) -> None:
        successful_installs, failed_installs = split_success_and_failure(
            results=self.outcome_summary.installed_packages,
            sindri_packages=self.sindri_packages,
        )
        successful_uninstalls, failed_uninstalls = split_success_and_failure(
            results=self.outcome_summary.uninstalled_packages,
            sindri_packages=self.sindri_packages,
        )
        install_package_status = self.outcome_summary.install_self
        uninstall_package_status = self.outcome_summary.uninstall_self
        log_manager.log_summary(
            title="Final Summary",
            message="Finished.",
            notes={
                "self-install": format_optional_outcome(install_package_status),
                "self-uninstall": format_optional_outcome(uninstall_package_status),
                "Successfully installed": format_list(successful_installs),
                "Successfully uninstalled": format_list(successful_uninstalls),
                "Failed to install": format_list(failed_installs),
                "Failed to uninstall": format_list(failed_uninstalls),
            },
        )
        status_summary: list[bool] = []
        if install_package_status is not None:
            status_summary.append(bool(install_package_status))
        if uninstall_package_status is not None:
            status_summary.append(bool(uninstall_package_status))
        status_summary.extend(
            successful for (_, successful) in self.outcome_summary.uninstalled_packages
            if successful is not None
        )
        status_summary.extend(
            successful for (_, successful) in self.outcome_summary.installed_packages
            if successful is not None
        )
        sys.exit(0 if all(status_summary) else 1)

    def run(
        self,
    ) -> None:
        self.parse_and_verify_args()
        self.apply_requested_actions()
        self.summarise_and_exit()


##
## === MAIN ===
##


def main():
    user_args = parse_args()
    LinkPackages(user_args).run()


if __name__ == "__main__":
    main()

## } SCRIPT
