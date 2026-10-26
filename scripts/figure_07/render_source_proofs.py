#!/usr/bin/env python3
"""Render current Figure 7A-D source proofs; C remains a labeled fit candidate."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'scripts/revision'))
from figures_567 import render
render(root, only='07')
