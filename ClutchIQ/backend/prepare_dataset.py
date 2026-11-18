
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW = PROJECT_DIR / "data" / "raw"
PROCESSED = PROJECT_DIR / "data" / "processed"

PROCESSED.mkdir(parents=True, exist_ok=True)

print("CLUTCHIQ DATA PREPARATION")

# Load original datasets
competitions = pd.read_csv(RAW / "competitions.csv")
matches = pd.read_csv(RAW / "matches.csv")
deliveries = pd.read_csv(RAW / "ball_by_ball.csv")

# Identify IPL and T20I competitions
is_ipl = competitions["comp_name"].str.fullmatch(
    r"IPL\s+\d{4}", case=False, na=False
)

is_t20i = competitions["match_format"].eq("T20I")

selected_competitions = competitions[
    is_ipl | is_t20i
].copy()

# Select corresponding matches
selected_matches = matches.merge(
    selected_competitions[
        ["comp_id", "comp_name", "match_format", "season"]
    ],
    on="comp_id",
    how="inner"
)

# Keep deliveries belonging to selected matches
match_ids = selected_matches["match_id"].unique()

selected_deliveries = deliveries[
    deliveries["match_id"].isin(match_ids)
].copy()

# Save processed datasets
selected_matches.to_csv(
    PROCESSED / "selected_matches.csv", index=False
)

selected_deliveries.to_csv(
    PROCESSED / "selected_deliveries.csv", index=False
)

# Display results
print("\nSelected competitions:", len(selected_competitions))
print("Selected matches:", len(selected_matches))
print("Selected deliveries:", len(selected_deliveries))

print("\nMatches by format:")
print(selected_matches["match_format"].value_counts())

print("\nSaved files:")
print("selected_matches.csv")
print("selected_deliveries.csv")

print("\nDATA PREPARATION COMPLETE!")
