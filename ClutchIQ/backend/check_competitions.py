
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

# Load competition and match information
competitions = pd.read_csv(DATA_DIR / "competitions.csv")
matches = pd.read_csv(DATA_DIR / "matches.csv")

# Identify IPL and T20I competitions
is_ipl = competitions["comp_name"].str.fullmatch(
    r"IPL\s+\d{4}", case=False, na=False
)

is_t20i = competitions["match_format"].eq("T20I")

selected = competitions[is_ipl | is_t20i].copy()

# Connect competitions with matches
selected_matches = matches.merge(
    selected[["comp_id", "comp_name", "match_format", "season"]],
    on="comp_id",
    how="inner"
)

print("\n========== CLUTCHIQ COMPETITION ANALYSIS ==========")

print("\nSelected competitions:", len(selected))
print("Selected matches:", len(selected_matches))

print("\nMatches by format:")
print(selected_matches["match_format"].value_counts())

print("\nMatches by competition:")
print(
    selected_matches.groupby("comp_name")
    .size()
    .to_string()
)

print("\nDate range:")
print("First match:", selected_matches["match_date"].min())
print("Last match:", selected_matches["match_date"].max())

print("\n========== ANALYSIS COMPLETE ==========")
