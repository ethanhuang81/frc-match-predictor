# FRC Strategy Analyzer (v1)

Predicts the probability that a 3-team alliance beats another 3-team
alliance, using [Statbotics](https://www.statbotics.io) EPA data. Works
for hypothetical groupings too, not just scheduled matches -- useful for
alliance selection scenarios.

## Setup

```bash
git clone <your-repo-url>
cd frc-strat-analyzer
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

That opens the app in your browser. Enter 3 team numbers for Red, 3 for
Blue, hit Predict.

## Project layout

- `epa_client.py` -- fetches team EPA from Statbotics via their official
  Python package
- `predictor.py` -- sums each alliance's EPA and converts the difference
  to a win probability with a logistic curve
- `app.py` -- the Streamlit UI
- `requirements.txt`, `.gitignore`

## A field-name caveat

Statbotics has changed their response shape across API versions before,
and I built this without being able to hit their live API to confirm the
exact current field name for a team-year's EPA. `epa_client.py` checks a
few likely field names in order (`_extract_epa()`), so it should work out
of the box -- but if you get a `TeamEpaError` on first run, do:

```bash
python epa_client.py
```

That prints the raw dict Statbotics returns for team 254. Find the EPA
field in there and add/reorder it in `_extract_epa()`. Should be a
one-line fix.

## Calibrating the win probability curve

`predictor.py` has a `SCALE` constant that controls how sharply an EPA
gap translates into a win probability. It's a reasonable starting guess,
not Statbotics' actual internal constant (they haven't published it).
Once you've got a season's worth of real match results, you can fit this
properly:

1. Pull matches for a year with `sb.get_matches(year=...)` (includes
   actual winners)
2. For each match, compute each alliance's summed EPA *at match time*
3. Fit `SCALE` so predicted probabilities match real outcomes (minimizing
   Brier score is the standard approach here)

Not needed for v1 -- just the natural next step once you want more than a
reasonable starting guess.

## Making data closer to real-time

See the "real-time" discussion in chat -- short version: lower or drop
`CACHE_TTL_SECONDS` in `app.py`, and know that you're ultimately bounded
by how often Statbotics itself recomputes EPA during a live event (they
update after each match result comes in from The Blue Alliance, not
continuously).
