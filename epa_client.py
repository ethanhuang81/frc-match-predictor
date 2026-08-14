"""
Thin wrapper around the official `statbotics` Python package.

No API key needed -- Statbotics' Python client hits their public REST API
(api.statbotics.io) directly. This module just adds:
  - a single shared client
  - a defensive EPA extractor (Statbotics has changed its response shape
    across API versions, so we don't hardcode one field path)
  - simple functions that are easy to wrap in Streamlit's own cache
    (see app.py) or call from a plain script
"""

from __future__ import annotations

from typing import Optional

import statbotics

_sb = statbotics.Statbotics()


class TeamEpaError(Exception):
    """Raised when a team/year lookup fails or has no usable EPA value."""


def _extract_epa(raw: dict) -> float:
    """
    Pull a single "current total EPA" number out of a get_team_year()
    response.

    Statbotics 3.x nests some fields (e.g. norm_epa: {current, recent,
    mean, max}) and exposes others flat (e.g. epa_end). Rather than
    assuming one exact shape, we check the likely candidates in order.

    If this raises, print the raw dict (see the bottom of this file) to
    see what Statbotics actually returned for your Python package version,
    and add the correct key here -- it's a one-line fix.
    """
    epa_field = raw.get("epa")
    candidates = [
        raw.get("epa_end"),
        epa_field.get("total_points", {}).get("mean") if isinstance(epa_field, dict) else None,
        epa_field.get("current") if isinstance(epa_field, dict) else None,
        epa_field if isinstance(epa_field, (int, float)) else None,
        raw.get("norm_epa", {}).get("current") if isinstance(raw.get("norm_epa"), dict) else None,
        raw.get("norm_epa") if isinstance(raw.get("norm_epa"), (int, float)) else None,
    ]
    for value in candidates:
        if isinstance(value, (int, float)):
            return float(value)

    raise TeamEpaError(
        f"Couldn't find an EPA value in the response: {raw}\n"
        "Statbotics may have changed its field names -- check the dict "
        "above for the right key and update _extract_epa() in epa_client.py."
    )


def get_team_epa(team_number: int, year: int) -> float:
    """Return a single team's total EPA for the given year."""
    try:
        raw = _sb.get_team_year(team_number, year)
    except Exception as exc:  # the statbotics client raises on 404s, bad team#, etc.
        raise TeamEpaError(f"Team {team_number} has no data for {year}: {exc}") from exc
    return _extract_epa(raw)


def get_team_name(team_number: int) -> Optional[str]:
    """Best-effort team nickname lookup, for a nicer UI. Returns None on failure."""
    try:
        return _sb.get_team(team_number).get("name")
    except Exception:
        return None


def get_latest_year(default: int) -> int:
    """
    Best-effort lookup of the most recent year Statbotics actually has data
    for -- rather than assuming it matches today's calendar year.

    This matters because a season can be over on the calendar before
    Statbotics has finished publishing that year's EPA data, and because
    the installed `statbotics` package version can occasionally lag the
    live API. If a query for a given year comes back as invalid, this is
    the first thing to suspect (see README).

    Falls back to `default` if the lookup itself fails for any reason.
    """
    try:
        years = _sb.get_years(metric="year", ascending=False, limit=1, fields=["year"])
        if years:
            return int(years[0]["year"])
    except Exception:
        pass
    return default


if __name__ == "__main__":
    # Diagnostic script: `python epa_client.py`
    #
    # Runs a few independent calls and prints full tracebacks on failure,
    # so we can see exactly which layer is broken instead of one flattened
    # error message. Send me everything this prints.
    import traceback

    print("statbotics package version:", getattr(statbotics, "__version__", "unknown"))

    print("\n--- Test 1: get_team(254) -- simplest possible call, no year involved ---")
    try:
        print(_sb.get_team(254))
    except Exception:
        traceback.print_exc()

    print("\n--- Test 2: get_years(limit=3) -- which years does Statbotics report? ---")
    try:
        print(_sb.get_years(limit=3, ascending=False))
    except Exception:
        traceback.print_exc()

    print("\n--- Test 3: get_team_year(254, 2025) -- a known-past, definitely-real season ---")
    try:
        print(_sb.get_team_year(254, 2025))
    except Exception:
        traceback.print_exc()
