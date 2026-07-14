"""
Central place that knows about every implemented Drill. The API layer
looks problems up here by drill_id instead of importing drill classes
directly, so adding a new drill only requires: (1) implement the class,
(2) add it to REGISTRY, (3) add its content/builtin-drills/<id>.json config.
"""

from __future__ import annotations

from app.drills.algebra import AlgebraicManipulationDrill
from app.drills.arithmetic import (
    AdditionDrill,
    CbrtsDrill,
    CubesDrill,
    DivisionDrill,
    MultiplicationDrill,
    SqrtsDrill,
    SquaresDrill,
    SubtractionDrill,
)
from app.drills.base import Drill
from app.drills.calculus import DerivativesDrill, IntegralsDrill
from app.drills.diffeq import OdePdeDrill
from app.drills.limits import LimitsDrill
from app.drills.linalg import RREFDrill
from app.drills.trig import TrigValuesDrill

REGISTRY: dict[str, Drill] = {
    d.id: d
    for d in [
        AdditionDrill(),
        SubtractionDrill(),
        MultiplicationDrill(),
        DivisionDrill(),
        SquaresDrill(),
        SqrtsDrill(),
        CubesDrill(),
        CbrtsDrill(),
        TrigValuesDrill(),
        AlgebraicManipulationDrill(),
        LimitsDrill(),
        DerivativesDrill(),
        IntegralsDrill(),
        RREFDrill(),
        OdePdeDrill(),
    ]
}


def get_drill(drill_id: str) -> Drill:
    if drill_id not in REGISTRY:
        raise KeyError(f"Unknown drill_id: {drill_id!r}. Known: {list(REGISTRY)}")
    return REGISTRY[drill_id]
