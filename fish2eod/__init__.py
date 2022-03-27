from fish2eod.analysis import plotting
from fish2eod.analysis.transdermal import compute_transdermal_potential
from fish2eod.geometry.primitives import *
from fish2eod.helpers.type_helpers import ElectricImageParameters
from fish2eod.math import BoundaryCondition
from fish2eod.models import BaseFishModel, QESModel
from fish2eod.sweep import (
    EODPhase,
    FishPosition,
    IterativeSolver,
    ParameterSet,
    ParameterSweep,
)
from fish2eod.xdmf.load import load_from_file

__version__ = "1.0a1"
