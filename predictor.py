"""
Win-probability model: sum each alliance's team EPAs, then run the
difference through a logistic curve.

This mirrors the shape of Statbotics' own match-prediction model -- an
alliance's rating is the sum of its three teams' ratings, and win
probability is a logistic function of the difference between the two
alliances (see statbotics.io/blog/epa). Statbotics hasn't published the
exact scale constant they use internally, so SCALE below is a starting
guess, not their real number. Treat it as a knob:

    Bigger SCALE  -> curve is "flatter" (closer matchups look closer to 50/50)
    Smaller SCALE -> curve is "steeper" (small EPA gaps swing win% harder)

Once you've got real match results for a season, you can calibrate this
by pulling matches via get_matches(), computing each alliance's EPA sum
at match time, and fitting SCALE so predicted probabilities line up with
actual outcomes (e.g. minimize Brier score). Not needed for v1 -- just
flagging it as the natural next step.
"""

from __future__ import annotations

import math

SCALE = 20.0


def alliance_epa(team_epas: list[float]) -> float:
    """Sum of a 3-team alliance's EPAs."""
    return sum(team_epas)


def win_probability(red_epas: list[float], blue_epas: list[float], scale: float = SCALE) -> float:
    """
    Probability the 'red' alliance beats the 'blue' alliance, given each
    alliance's list of 3 team EPAs. Returns a value in (0, 1).
    """
    diff = alliance_epa(red_epas) - alliance_epa(blue_epas)
    return 1.0 / (1.0 + math.exp(-diff / scale))
