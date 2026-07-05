"""
Central place that knows about every implemented Drill. The API layer
looks problems up here by drill_id instead of importing drill classes
directly, so adding a new drill only requires: (1) implement the class,
(2) add it to REGISTRY, (3) add its content/builtin-drills/<id>.json config.
"""

from __future__ import annotations

from app.drills.arithmetic import AdditionDrill, SubtractionDrill
from app.drills.base import Drill
from app.drills.calculus import DerivativesDrill

REGISTRY: dict[str, Drill] = {
    d.id: d
    for d in [
        AdditionDrill(),
        SubtractionDrill(),
        DerivativesDrill(),
        # TODO: MultiplicationDrill, DivisionDrill, SquaresDrill, SqrtsDrill,
        #       CubesDrill, CbrtsDrill, TrigValuesDrill, AlgebraicManipulationDrill,
        #       IntegralsDrill, RREFDrill, OdePdeDrill -- once implemented in
        #       app/drills/*.py, register them here.
    ]
}


def get_drill(drill_id: str) -> Drill:
    if drill_id not in REGISTRY:
        raise KeyError(f"Unknown drill_id: {drill_id!r}. Known: {list(REGISTRY)}")
    return REGISTRY[drill_id]
