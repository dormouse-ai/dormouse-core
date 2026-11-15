"""dormouse-core: the discipline layer.

Counters that turn a silent mechanism into a hard error, coeffects that refuse an
incompatible component before it allocates, reversible effects that restore the
context exactly, and errors that name the way out.
"""

from .coeffects import Coeffects
from .component import Component, ComponentError
from .counters import Counters, MissingReport
from .effect import Effect
from .errors import DormouseError, LoudError
from .order import topo_order
from .slot import Slot

__all__ = [
    "Coeffects",
    "Component",
    "ComponentError",
    "Counters",
    "DormouseError",
    "Effect",
    "LoudError",
    "MissingReport",
    "Slot",
    "topo_order",
]
