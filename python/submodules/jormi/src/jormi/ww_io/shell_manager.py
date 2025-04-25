## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import shlex
import subprocess


## ###############################################################
## FUNCTIONS
## ###############################################################
def does_shell_command_require_privileges(command):
  special_shell_tokens = {
    "|",        # pipe: `ls | grep .py`
    # "&",      # background execution: `sleep 5 &`
    # ";",      # command separator: `cmd1; cmd2`
    "<",        # input redirection: `sort < file.txt`
    ">",        # output redirection: `echo "hi" > file.txt`
    # "(", ")", # subshell execution: `(cd /tmp && ls)`
    "$",        # variable expansion: `echo $HOME`
    "*", "?",   # wildcards: `rm *.txt`, `ls file?.txt`
    # "#",      # comment: `echo hello # ignored part`
    # "{", "}", # brace expansion: `echo {a,b,c}`
    # "=",      # variable assignment: `VAR=value`
    # "[", "]", # test conditions: `[ -f file.txt ]`
    # "~",      # home directory: `cd ~`
  }
  return any(
    word in special_shell_tokens
    for word in command
  )

def execute_shell_command(
    command           : str,
    working_directory : str | None = None,
    timeout_seconds   : float = 15,
    capture_output    : bool  = True,
    enforce_shell     : bool  = False,
  ) -> str:
  is_shell_required = enforce_shell or does_shell_command_require_privileges(command)
  try:
    result = subprocess.run(
      command if is_shell_required else shlex.split(command),
      cwd            = working_directory,
      timeout        = timeout_seconds,
      capture_output = True,
      shell          = is_shell_required,
      check          = False,
      text           = True,
    )
  except FileNotFoundError as exception:
    raise RuntimeError(f"Command `{command}` could not be executed.") from exception
  except subprocess.TimeoutExpired as exception:
    raise RuntimeError(f"Command `{command}` timed out after `{timeout_seconds}` seconds.") from exception
  if result.returncode != 0:
    error_message = f"The following command failed with return code `{result.returncode}`: {command}"
    if result.stdout: error_message += f"\nstdout: {result.stdout.strip()}"
    if result.stderr: error_message += f"\nstderr: {result.stderr.strip()}"
    raise RuntimeError(error_message)
  return result.stdout.strip() if capture_output else ""


## END OF MODULE