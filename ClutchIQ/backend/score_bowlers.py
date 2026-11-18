
import csv
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

SOURCE = BASE / "data" / "processed" / "bowler_pressure_rankings.csv"
OUTPUT = BASE / "data" / "processed" / "clutchiq_bowler_scores.csv"

MIN_BALLS = 60
RELIABILITY_TARGET = 120


def percentile_ranks(values):
    ordered = sorted(values)
    n = len(ordered)

    if n == 1:
        return [50.0]

    ranks = []

    for value in values:
        less = sum(1 for x in ordered if x < value)
        equal = sum(1 for x in ordered if x == value)

        rank = (
            less + (equal - 1) / 2
        ) / (n - 1) * 100

        ranks.append(rank)

    return ranks


# Load bowling pressure statistics
with open(SOURCE, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))


# Apply minimum sample requirements
qualified = [
    r for r in rows
    if int(r["pressure_legal_balls"]) >= MIN_BALLS
    and int(r["normal_legal_balls"]) >= MIN_BALLS
]

if not qualified:
    raise ValueError(
        "No bowlers meet the minimum sample requirements."
    )


# Calculate wicket-rate improvement
for r in qualified:
    pressure_balls = int(r["pressure_legal_balls"])
    normal_balls = int(r["normal_legal_balls"])

    pressure_wicket_rate = (
        int(r["pressure_wickets"]) / pressure_balls * 100
    )

    normal_wicket_rate = (
        int(r["normal_wickets"]) / normal_balls * 100
    )

    r["wicket_rate_improvement"] = (
        pressure_wicket_rate - normal_wicket_rate
    )

    r["dot_rate_improvement"] = (
        float(r["pressure_dot_pct"])
        - float(r["normal_dot_pct"])
    )


# Scoring weights
metrics = {
    "economy_improvement": 0.40,
    "wicket_rate_improvement": 0.30,
    "dot_rate_improvement": 0.30
}


# Calculate percentile scores
for metric, weight in metrics.items():
    values = [float(r[metric]) for r in qualified]

    ranks = percentile_ranks(values)

    for row, rank in zip(qualified, ranks):
        row[metric + "_percentile"] = rank


# Calculate final ClutchIQ scores
for r in qualified:

    raw_score = sum(
        r[metric + "_percentile"] * weight
        for metric, weight in metrics.items()
    )

    pressure_balls = int(r["pressure_legal_balls"])
    normal_balls = int(r["normal_legal_balls"])

    sample_size = min(
        pressure_balls,
        normal_balls
    )

    reliability = min(
        1.0,
        math.sqrt(sample_size / RELIABILITY_TARGET)
    )

    r["reliability"] = round(reliability, 3)

    r["clutchiq_score"] = round(
        raw_score * reliability,
        2
    )


# Sort highest score first
qualified.sort(
    key=lambda r: r["clutchiq_score"],
    reverse=True
)


# Export fields
fields = [
    "player",
    "clutchiq_score",
    "pressure_legal_balls",
    "normal_legal_balls",
    "pressure_economy",
    "normal_economy",
    "pressure_wickets",
    "normal_wickets",
    "pressure_dots",
    "normal_dots",
    "pressure_dot_pct",
    "normal_dot_pct",
    "economy_improvement",
    "wicket_rate_improvement",
    "dot_rate_improvement",
    "reliability"
]


# Save results (single CSV export)
with open(OUTPUT, "w", encoding="utf-8", newline="") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fields
    )

    writer.writeheader()

    for row in qualified:
        writer.writerow({
            key: row.get(key, "")
            for key in fields
        })


# Display leaderboard
print("\nCLUTCHIQ BOWLING LEADERBOARD")

print("Qualified bowlers:", len(qualified))

print("-" * 65)

for i, r in enumerate(qualified[:10], 1):

    print(
        f"{i}. {r['player']}"
        f" | ClutchIQ: {r['clutchiq_score']}"
        f" | Pressure Econ: {r['pressure_economy']}"
        f" | Normal Econ: {r['normal_economy']}"
        f" | Pressure Wickets: {r['pressure_wickets']}"
        f" | Pressure Balls: {r['pressure_legal_balls']}"
        f" | Reliability: {r['reliability']}"
    )

print("\nSaved:", OUTPUT)

