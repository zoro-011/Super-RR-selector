import csv
from pathlib import Path

f = Path(__file__).resolve().parent.parent / "data/processed/bowler_pressure_rankings.csv"

with open(f, encoding="utf-8-sig") as file:
    rows = list(csv.DictReader(file))

qualified = [
    r for r in rows
    if int(r["pressure_legal_balls"]) >= 60
    and int(r["normal_legal_balls"]) >= 60
]

print("QUALIFIED BOWLERS:", len(qualified))

for r in qualified:
    print(
        r["player"],
        "| Pressure economy:", r["pressure_economy"],
        "| Improvement:", r["economy_improvement"],
        "| Wickets:", r["pressure_wickets"]
    )