def compute_plasma_params(
    k_turb : float,
    mach   : float,
    Re     : float | None = None,
    Rm     : float | None = None,
    Pm     : float | None = None
  ):
  if (Re is not None) and (Pm is not None):
    Re  = float(Re)
    Pm  = float(Pm)
    Rm  = Re * Pm
    nu  = round(mach / (k_turb * Re), 5)
    eta = round(nu / Pm, 5)
  elif (Rm is not None) and (Pm is not None):
    Rm  = float(Rm)
    Pm  = float(Pm)
    Re  = Rm / Pm
    nu  = round(eta * Pm, 5)
    eta = round(mach / (k_turb * Rm), 5)
  else: raise Exception(f"Error: insufficient plasma Reynolds numbers provided: Re = {Re}, Rm = {Rm}, Pm = {Rm}")
  return {
    "nu"  : nu,
    "eta" : eta,
    "Re"  : Re,
    "Rm"  : Rm,
    "Pm"  : Pm
  }

