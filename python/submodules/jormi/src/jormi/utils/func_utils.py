## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################
import time
import inspect
import warnings


## ###############################################################
## FUNCTION DECORATORS
## ###############################################################
def time_function(func):
  def wrapper(*args, **kwargs):
    start_time = time.time()
    try:
      result = func(*args, **kwargs)
    except Exception as error:
      raise RuntimeError(f"Error occurred in {func.__name__}() while measuring the elapsed time.") from error
    elapsed_time = time.time() - start_time
    print(f"{func.__name__}() took {elapsed_time:.3f} seconds to execute.")
    return result
  return wrapper

def warn_if_result_is_unused(func):
  def wrapper(*args, **kwargs):
    result = func(*args, **kwargs)
    ## check that the result is being assigned
    calling_frame = inspect.currentframe().f_back # type: ignore
    call_line = inspect.getsource(calling_frame).split("\n")[calling_frame.f_lineno - calling_frame.f_code.co_firstlineno] # type: ignore
    if ("=" not in call_line) and ("return" not in call_line) and (result is not None):
      warnings.warn(f"Return value of {func.__name__}() is not being used", UserWarning, stacklevel=2)
    return result
  return wrapper


## END OF MODULE