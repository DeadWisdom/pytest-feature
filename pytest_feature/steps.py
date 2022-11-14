registry = {}

def step(name):
  def decorator(fn):
    registry[name.strip().lower()] = fn
    return fn
  return decorator

def get_step(name):
  name = name.strip().lower()
  try:
    return registry[name]
  except KeyError:
    raise NoStepError(name)

class NoStepError(NameError):
  pass
