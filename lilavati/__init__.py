"""Lilavati: a 95M-parameter model that solves maths word problems by writing and running Python (UdgamLabs)."""
from .solve import Lilavati
from .safe_exec import run, check_program

__all__ = ["Lilavati", "run", "check_program"]
