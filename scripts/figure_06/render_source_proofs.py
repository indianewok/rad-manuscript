#!/usr/bin/env python3
"""Render Figure 6 source proofs from portable tables; preserve selected stats."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'scripts/revision'))
from figures_567 import render
render(root, only='06')
