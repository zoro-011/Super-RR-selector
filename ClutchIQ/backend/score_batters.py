
import csv
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "batter_pressure_rankings.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "clutchiq_batter_scores.csv"

MIN_PRESSURE_BALLS = 30
RELIABILITY_TARGET = 120


def percentile_ranks(values):
    ordered = sorted(values)
    count = len(ordered)

    if count <= 1:
        return [100.0] * count

    return [
        (sum(v <= value for v in ordered) - 1) / (count - 1) * 100
        for value in values
    ]


with open(INPUT_FILE, encoding="utf-8-sig", newline="") as f:
    batters = list(csv.DictReader(f))

# Keep batters with a minimum pressure sample.
qualified = [
    b for b in batters
    if int(b["pressure_balls"]) >= MIN_PRESSURE_BALLS
]

if not qualified:
    raise ValueError("No batters meet the minimum pressure-ball requirement.")

# Convert metrics to numbers.
for b in qualified:
    b["pressure_runs"] = int(b["pressure_runs"])
    b["pressure_balls"] = int(b["pressure_balls"])
    b["pressure_dismissals"] = int(b["pressure_dismissals"])
    b["pressure_strike_rate"] = float(b["pressure_strike_rate"])
    b["normal_strike_rate"] = float(b["normal_strike_rate"])
    b["strike_rate_difference"] = float(b["strike_rate_difference"])

# Calculate percentiles across qualified batters.
sr_improvement = percentile_ranks(
    [b["strike_rate_difference"] for b in qualified]
)
pressure_sr = percentile_ranks(
    [b["pressure_strike_rate"] for b in qualified]
)
pressure_runs = percentile_ranks(
    [b["pressure_runs"] for b in qualified]
)

for i, b in enumerate(qualified):
    raw_score = (
        sr_improvement[i] * 0.50
        + pressure_sr[i] * 0.30
        + pressure_runs[i] * 0.20
    )

    reliability = min(
        1.0,
        math.sqrt(b["pressure_balls"] / RELIABILITY_TARGET)
    )

    b["raw_score"] = raw_score
    b["reliability"] = reliability
    b["clutchiq_score"] = raw_score * reliability

qualified.sort(
    key=lambda b: b["clutchiq_score"],
    reverse=True
)

fields = [
    "player",
    "clutchiq_score",
    "raw_score",
    "pressure_runs",
    "pressure_balls",
    "pressure_strike_rate",
    "normal_strike_rate",
    "strike_rate_difference",
    "pressure_dismissals",
    "reliability"
]

with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()

    for b in qualified:
        row = {
            key: round(b[key], 2) if isinstance(b[key], float) else b[key]
            for key in fields
        }
        writer.writerow(row)

print("\nCLUTCHIQ TOP 10 BATTERS")
print("-" * 65)

for i, b in enumerate(qualified[:10], 1):
    print(
        f"{i}. {b['player']} | "
        f"Score: {b['clutchiq_score']:.2f} | "
        f"Pressure SR: {b['pressure_strike_rate']:.2f} | "
        f"Pressure Runs: {b['pressure_runs']} | "
        f"Balls: {b['pressure_balls']}"
    )

print(f"\nQualified batters: {len(qualified)}")
print(f"Saved to: {OUTPUT_FILE}")
