## { SCRIPT

##
## === DEPENDENCIES
##

## stdlib
import argparse
import os
import shutil
import sys
import typing
from pathlib import Path

## third-party
import libcst
from jormi.ww_io import manage_log, manage_shell

##
## === GLOBAL PARAMS
##

SCRIPT_DIR = Path(__file__).resolve().parent
STYLE_FILE_NAME = ".style.yapf"
STYLE_FILE_PATH = SCRIPT_DIR / STYLE_FILE_NAME
FILES_TO_IGNORE: set[str] = set()
DIRS_TO_IGNORE: tuple[str, ...] = (
    ".DS_Store",
    "__pycache__",
    ".venv",
    ".git",
    "build",
    "dist",
    ".eggs",
)

##
## === HELPER FUNCTIONS
##


def ensure_styling_rules_exist() -> None:
    if not STYLE_FILE_PATH.exists():
        manage_log.log_error(
            f"Style file `{STYLE_FILE_NAME}` not found next to this script.",
            notes={"expected_path": str(STYLE_FILE_PATH)},
        )
        sys.exit(1)


def ensure_uv_is_available() -> None:
    ## checking for uv is fine, since uvx is a subcommand of it
    if shutil.which("uv") is None:
        manage_log.log_error("`uv` not found in PATH. Install uv first.")
        sys.exit(1)
    manage_log.log_outcome("Found `uv`", outcome=manage_log.ActionOutcome.SUCCESS)


def should_ignore_dirname(
    dir_name: str,
) -> bool:
    return dir_name in DIRS_TO_IGNORE


def should_ignore_file(
    path: Path,
) -> bool:
    if path.name in FILES_TO_IGNORE:
        return True
    if path.suffix.lower() != ".py":
        return True
    if any(path_part in DIRS_TO_IGNORE for path_part in path.parts):
        return True
    return False


def collect_py_files(
    paths: list[Path],
) -> list[Path]:
    py_paths: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            if not should_ignore_file(path):
                py_paths.append(path)
            continue
        for dir_path, dir_names, file_names in os.walk(path, topdown=True):
            dir_names[:] = [
                dir_name
                for dir_name in dir_names
                if not should_ignore_dirname(dir_name)
            ]
            for file_name in file_names:
                full_path = Path(dir_path) / file_name
                if should_ignore_file(full_path):
                    continue
                py_paths.append(full_path)
    py_paths.sort()
    return py_paths


class AddTrailingCommas(libcst.CSTTransformer):
    def leave_FunctionDef(
        self,
        original_node: libcst.FunctionDef,
        updated_node: libcst.FunctionDef,
    ) -> libcst.FunctionDef:
        return updated_node.with_changes(
            params=ensure_trailing_comma(updated_node.params),
        )


def ensure_trailing_comma(
    params: libcst.Parameters,
) -> libcst.Parameters:
    comma: libcst.Comma = libcst.Comma(whitespace_after=libcst.SimpleWhitespace(""))
    if params.star_kwarg is not None:
        if isinstance(params.star_kwarg.comma, libcst.MaybeSentinel):
            return params.with_changes(
                star_kwarg=params.star_kwarg.with_changes(comma=comma),
            )
    elif params.kwonly_params:
        last = params.kwonly_params[-1]
        if isinstance(last.comma, libcst.MaybeSentinel):
            return params.with_changes(
                kwonly_params=(
                    *params.kwonly_params[:-1],
                    last.with_changes(comma=comma),
                ),
            )
    elif params.params:
        last = params.params[-1]
        if isinstance(last.comma, libcst.MaybeSentinel):
            return params.with_changes(
                params=(*params.params[:-1], last.with_changes(comma=comma)),
            )
    elif params.posonly_params:
        last = params.posonly_params[-1]
        if isinstance(last.comma, libcst.MaybeSentinel):
            return params.with_changes(
                posonly_params=(
                    *params.posonly_params[:-1],
                    last.with_changes(comma=comma),
                ),
            )
    return params


def apply_fn_signature_expansion(
    py_paths: list[Path],
) -> None:
    if not py_paths:
        manage_log.log_note("No Python files to expand function signatures")
        return
    manage_log.log_task(
        f"Expanding function signatures to multi-line ({len(py_paths)} files)",
    )
    transformer = AddTrailingCommas()
    for file_path in py_paths:
        source = file_path.read_text(encoding="utf-8")
        new_source = libcst.parse_module(source).visit(transformer).code
        if new_source != source:
            _ = file_path.write_text(new_source, encoding="utf-8")
    manage_log.log_outcome(
        "Completed function signature expansion",
        outcome=manage_log.ActionOutcome.SUCCESS,
    )


def apply_trailing_commas_to_multiline(
    py_paths: list[Path],
) -> None:
    if not py_paths:
        manage_log.log_note("No Python files to update for trailing commas")
        return
    manage_log.log_task(f"Adding trailing commas where safe ({len(py_paths)} files)")
    for file_path in py_paths:
        _ = manage_shell.execute_shell_command(
            f'uvx --from add-trailing-comma add-trailing-comma --exit-zero-even-if-changed "{file_path}"',
            timeout_seconds=120,
        )
    manage_log.log_outcome(
        "Completed trailing-commas pass",
        outcome=manage_log.ActionOutcome.SUCCESS,
    )


def apply_yapf_style(
    py_paths: list[Path],
) -> None:
    if not py_paths:
        manage_log.log_note("No files for YAPF")
        return
    if not STYLE_FILE_PATH.exists():
        manage_log.log_error(
            f"Style file `{STYLE_FILE_NAME}` was not found next to this script.",
            notes={"expected_path": str(STYLE_FILE_PATH)},
        )
        sys.exit(1)
    manage_log.log_task(f"Running YAPF-styling on {len(py_paths)} file(s)")
    for file_path in py_paths:
        _ = manage_shell.execute_shell_command(
            f'uvx --from yapf yapf -i --verbose --style "{STYLE_FILE_PATH}" "{file_path}"',
            timeout_seconds=300,
        )
    manage_log.log_outcome(
        "Completed YAPF formatting",
        outcome=manage_log.ActionOutcome.SUCCESS,
    )


##
## === MAIN ROUTINE
##


def format_project(
    paths: list[str] | None = None,
) -> int:
    manage_log.log_task("Formatting Python files...", show_time=True)
    ensure_styling_rules_exist()
    ensure_uv_is_available()
    manage_log.log_note(f"Using style rules from: {STYLE_FILE_PATH}")
    if not paths:
        resolved_targets = [Path.cwd()]
    else:
        resolved_targets = [Path(target).resolve() for target in paths]
    manage_log.log_note(
        "Scanning target roots: " + ", ".join(map(str, resolved_targets)),
    )
    py_paths = collect_py_files(resolved_targets)
    manage_log.log_note(
        f"Found {len(py_paths)} Python files across {len(resolved_targets)} target(s)",
    )
    if not py_paths:
        manage_log.log_note(
            "No Python files were found under: "
            + ", ".join(map(str, resolved_targets)),
        )
        manage_log.log_outcome(
            "Nothing to do",
            outcome=manage_log.ActionOutcome.SKIPPED,
        )
        return 0
    apply_trailing_commas_to_multiline(py_paths)
    apply_fn_signature_expansion(py_paths)
    apply_yapf_style(py_paths)
    manage_log.log_outcome(
        "Formatting finished",
        outcome=manage_log.ActionOutcome.SUCCESS,
    )
    return 0


##
## === USER INTERFACE
##


def main(
    argv: list[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(description="Format python files.")
    _ = parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "Folders or files to format. "
            "If none are provided, the current working directory is scanned and formatted. "
            "If provided, paths are resolved relative to your current working directory; "
            "absolute paths are also accepted."
        ),
    )
    args = parser.parse_args(argv if (argv is not None) else sys.argv[1:])
    return format_project(typing.cast(list[str], args.paths))


##
## === ENTRY POINT
##

if __name__ == "__main__":
    raise SystemExit(main())

## } SCRIPT
