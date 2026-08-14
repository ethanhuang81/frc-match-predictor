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


if __name__ == "__main__":
    # Quick manual check: `python epa_client.py` prints the raw response
    # for team 254 so you can confirm _extract_epa() is reading the right
    # field for the statbotics package version you have installed.
    import datetime

    year = datetime.date.today().year
    print(_sb.get_team_year(254, year))
    print("Extracted EPA:", get_team_epa(254, year))
