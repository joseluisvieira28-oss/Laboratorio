"""Canonical irregular-grid slope/curvature helpers for LCOD-001."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True)
class CurveGeometry:
    interval_slopes: tuple[float, ...]
    interior_curvatures: tuple[float, ...]

def irregular_grid_geometry(x_pp: Sequence[float], y: Sequence[float]) -> CurveGeometry:
    if len(x_pp) != len(y):
        raise ValueError("x/y length mismatch")
    if len(x_pp) < 3:
        raise ValueError("need >=3 points")
    x=tuple(float(v) for v in x_pp); yy=tuple(float(v) for v in y)
    if any(b <= a for a,b in zip(x,x[1:])):
        raise ValueError("x must be strictly increasing")
    slopes=tuple((yy[i]-yy[i-1])/(x[i]-x[i-1]) for i in range(1,len(x)))
    curv=[]
    for i in range(1,len(x)-1):
        left=(yy[i]-yy[i-1])/(x[i]-x[i-1])
        right=(yy[i+1]-yy[i])/(x[i+1]-x[i])
        curv.append(2.0*(right-left)/(x[i+1]-x[i-1]))
    return CurveGeometry(slopes,tuple(curv))
