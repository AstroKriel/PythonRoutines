## START OF MODULE


## ###############################################################
## FUNCTIONS
## ###############################################################
def assert_type(
    obj,
    required_types: type | tuple[type, ...],
    obj_name: str | None = None,
  ):
  """Assert that an object is of a specific type."""
  if not required_types: raise ValueError("No required types were passed.")
  if obj_name is None: obj_name = "<name not provided>"
  ## isinstance() accepts either a single instance or a tuple of instances
  if   isinstance(required_types, type): required_types = (required_types,)
  elif isinstance(required_types, list): required_types = tuple(required_types)
  if not isinstance(obj, required_types):
    type_names = ", ".join(
      required_type.__name__
      for required_type in required_types
    )
    raise TypeError(f"Variable `{obj_name}` is of type `{type(obj).__name__}` instead of `{type_names}`.")


## END OF MODULE