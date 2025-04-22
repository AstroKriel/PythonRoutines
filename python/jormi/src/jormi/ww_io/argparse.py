## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import sys
import argparse


## ###############################################################
## FUNCTIONS
## ###############################################################
class MyHelpFormatter(argparse.RawDescriptionHelpFormatter):
  def _format_action(self, action):
    formatted = super()._format_action(action)
    if action.nargs == argparse.PARSER:
      formatted = "\n".join(formatted.split("\n")[1:])
    return formatted

class MyParser(argparse.ArgumentParser):
  def __init__(self, description, epilog=None):
    super(MyParser, self).__init__(
      description     = description,
      epilog          = epilog,
      formatter_class = lambda prog: MyHelpFormatter(prog, max_help_position=50),
    )

  def error(self, message):
    sys.stderr.write(f"Error: {message}\n\n")
    self.print_help()
    sys.exit(2)

  def create_sub_group(self, title=None, description=None):
    return self.add_argument_group(title=title, description=description)

  def add_argument(self, group, name, type=None, is_bool=False, is_required=False, **kwargs):
    if group is None: group = self
    dict_arg_settings = { "help" : "type: %(type)s, default: %(default)s" }
    if (type is None) and not(is_bool): raise ValueError(f"You need to define a `type` for argument `{name}`.")
    if is_bool:
      dict_arg_settings["action"]   = "store_true"
      dict_arg_settings["default"]  = False
    else: dict_arg_settings["type"] = type
    group.add_argument(name, **{**dict_arg_settings, "required": is_required, **kwargs})


## END OF MODULE