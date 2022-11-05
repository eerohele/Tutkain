import sys

# Ensure all Python modules are reloaded when Package Control updates the
# package.
for module in list(
    filter(
        lambda name: name.startswith(__package__ + ".") and name != __name__,
        sys.modules,
    )
):
    del sys.modules[module]


from .api import *
from .src.core import *
