"""
FRC Strategy Analyzer -- V1

Enter 3 team numbers per alliance, get a predicted win probability based
on summed Statbotics EPA. Run with:

    streamlit run app.py
"""

from __future__ import annotations

import datetime

import streamlit as st

from epa_client import TeamEpaError, get_team_epa, get_team_name
from predictor import win_probability

CURRENT_YEAR = datetime.date.today().year

# How long to keep a team's EPA cached before re-fetching. Lower this (or
# see the README's "real-time" section) if you want fresher data during a
# live event.
CACHE_TTL_SECONDS = 3600

st.set_page_config(page_title="FRC Strategy Analyzer", page_icon="\U0001F916")

st.title("FRC Strategy Analyzer")
st.caption("Predicts win probability for a 3-team alliance vs. another, using Statbotics EPA.")

year = st.number_input("Season year", min_value=2002, max_value=CURRENT_YEAR, value=CURRENT_YEAR, step=1)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def cached_epa(team: int, yr: int) -> float:
    return get_team_epa(team, yr)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def cached_name(team: int) -> str | None:
    return get_team_name(team)


def team_inputs(label: str, key_prefix: str) -> list[int | None]:
    st.subheader(label)
    cols = st.columns(3)
    teams = []
    for i, col in enumerate(cols):
        with col:
            teams.append(
                st.number_input(
                    f"Team {i + 1}",
                    min_value=1,
                    step=1,
                    value=None,
                    placeholder="e.g. 254",
                    key=f"{key_prefix}_{i}",
                )
            )
    return teams


red_teams = team_inputs("Red Alliance", "red")
blue_teams = team_inputs("Blue Alliance", "blue")

if st.button("Predict", type="primary"):
    if any(t is None for t in red_teams + blue_teams):
        st.warning("Enter all 6 team numbers first.")
        st.stop()

    red_teams = [int(t) for t in red_teams]
    blue_teams = [int(t) for t in blue_teams]

    try:
        red_epas, blue_epas = [], []

        for team in red_teams:
            epa = cached_epa(team, int(year))
            red_epas.append(epa)
            st.write(f"\U0001F534 Team {team} ({cached_name(team) or '?'}): {epa:.1f} EPA")

        for team in blue_teams:
            epa = cached_epa(team, int(year))
            blue_epas.append(epa)
            st.write(f"\U0001F535 Team {team} ({cached_name(team) or '?'}): {epa:.1f} EPA")

        prob = win_probability(red_epas, blue_epas)

        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("Red Alliance win probability", f"{prob:.0%}")
        col2.metric("Blue Alliance win probability", f"{1 - prob:.0%}")

    except TeamEpaError as e:
        st.error(str(e))
