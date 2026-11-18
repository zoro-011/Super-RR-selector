
import csv
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent

DELIVERIES_FILE = BASE / "data" / "processed" / "selected_deliveries.csv"
MATCHES_FILE = BASE / "data" / "processed" / "selected_matches.csv"
OUTPUT = BASE / "data" / "processed"

BOWLER_WICKETS = {
    "Bowled", "Caught", "Stump", "LBW", "Hit Wicket"
}


def number(value, default=0):
    try:
        return float(value) if value not in ("", None) else default
    except (ValueError, TypeError):
        return default


def read_matches():
    matches = {}

    with open(MATCHES_FILE, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):

            # This dataset field is being treated as balls, not overs.
            max_balls = number(
                row.get("second_inn_revised_overs"), 120
            )

            if max_balls <= 0:
                max_balls = 120

            matches[row["match_id"]] = {
                "max_balls": int(max_balls),
                "revised_target": number(row.get("revised_target"))
            }

    return matches


def create_stats():
    return {
        "pressure_runs": 0,
        "pressure_balls": 0,
        "pressure_outs": 0,
        "normal_runs": 0,
        "normal_balls": 0,
        "normal_outs": 0,
        "pressure_legal": 0,
        "normal_legal": 0,
        "pressure_conceded": 0,
        "normal_conceded": 0,
        "pressure_wickets": 0,
        "normal_wickets": 0,
        "pressure_dots": 0,
        "normal_dots": 0
    }


def calculate():

    matches = read_matches()
    innings_data = defaultdict(list)

    with open(DELIVERIES_FILE, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):

            innings = int(number(row["innings"]))

            if innings in (1, 2) and row["match_id"] in matches:
                innings_data[(row["match_id"], innings)].append(row)

    batters = defaultdict(create_stats)
    bowlers = defaultdict(create_stats)
    names = {}

    processed = 0

    for match_id, info in matches.items():

        first = innings_data.get((match_id, 1), [])
        second = innings_data.get((match_id, 2), [])

        if not first or not second:
            continue

        first_total = sum(
            number(r["runs"])
            + number(r["extras1_runs"])
            + number(r["extras_2_runs"])
            for r in first
        )

        target = info["revised_target"]

        if target <= 0:
            target = first_total + 1

        max_balls = info["max_balls"]

        score = 0
        wickets_lost = 0
        legal_balls = 0

        for row in second:

            striker_id = row["striker_id"]
            striker = row["striker_name"]
            bowler = row["bowler_name"]

            names[striker_id] = striker
            names[row["non_striker_id"]] = row["non_striker_name"]

            extras_type = row["extras_type"].strip().lower()

            batter_runs = int(number(row["runs"]))
            extra1 = int(number(row["extras1_runs"]))
            extra2 = int(number(row["extras_2_runs"]))

            total_runs = batter_runs + extra1 + extra2

            # Calculate pressure before the current delivery.
            balls_remaining = max(0, max_balls - legal_balls)
            runs_needed = max(0, target - score)

            required_rate = (
                runs_needed * 6 / balls_remaining
                if balls_remaining > 0 else 0
            )

            pressure = (
                required_rate >= 10
                or (wickets_lost >= 6 and balls_remaining <= 60)
            )

            category = "pressure" if pressure else "normal"

            # Batter statistics.
            b = batters[striker]

            b[f"{category}_runs"] += batter_runs

            # Wides do not count as batter balls faced.
            if extras_type != "wide":
                b[f"{category}_balls"] += 1

            # Wides and oversteps are provisionally treated as illegal.
            legal = extras_type not in ("wide", "overstep")

            # Bowler runs conceded.
            # Byes, legbyes and penalties are excluded.
            bowler_runs = total_runs

            if extras_type in ("byes", "legbyes", "penalty"):
                bowler_runs -= extra1 + extra2

            w = bowlers[bowler]

            w[f"{category}_conceded"] += bowler_runs

            if legal:
                w[f"{category}_legal"] += 1

            if total_runs == 0:
                w[f"{category}_dots"] += 1

            # Wicket statistics.
            is_wicket = (
                row["is_wicket"].strip().lower() == "true"
            )

            dismissal = row["dismissal_type"].strip()

            if is_wicket:

                dismissed_id = row["dismissed_player_id"]

                if dismissed_id:
                    dismissed_name = names.get(
                        dismissed_id, striker
                    )

                    batters[dismissed_name][
                        f"{category}_outs"
                    ] += 1

                if dismissal in BOWLER_WICKETS:
                    w[f"{category}_wickets"] += 1

            # Update innings state after the delivery.
            score += total_runs

            if is_wicket:
                wickets_lost += 1

            if legal:
                legal_balls += 1

            processed += 1

    # ---------------------------------
    # SAVE BATTING STATISTICS
    # ---------------------------------

    batting_results = []

    for player, s in batters.items():

        if s["pressure_balls"] < 30 or s["normal_balls"] < 30:
            continue

        pressure_sr = (
            s["pressure_runs"] * 100 / s["pressure_balls"]
        )

        normal_sr = (
            s["normal_runs"] * 100 / s["normal_balls"]
        )

        batting_results.append({
            "player": player,
            "pressure_runs": s["pressure_runs"],
            "pressure_balls": s["pressure_balls"],
            "pressure_strike_rate": round(pressure_sr, 2),
            "normal_strike_rate": round(normal_sr, 2),
            "strike_rate_difference": round(
                pressure_sr - normal_sr, 2
            ),
            "pressure_dismissals": s["pressure_outs"]
        })

    batting_results.sort(
        key=lambda x: x["strike_rate_difference"],
        reverse=True
    )

    # ---------------------------------
    # SAVE BOWLING STATISTICS
    # ---------------------------------

    bowling_results = []

    for player, s in bowlers.items():

        if s["pressure_legal"] < 12 or s["normal_legal"] < 12:
            continue

        pressure_economy = (
            s["pressure_conceded"] * 6 / s["pressure_legal"]
        )

        normal_economy = (
            s["normal_conceded"] * 6 / s["normal_legal"]
        )

        pressure_dot_pct = (
            s["pressure_dots"] * 100 / s["pressure_legal"]
        )

        normal_dot_pct = (
            s["normal_dots"] * 100 / s["normal_legal"]
        )

        bowling_results.append({
            "player": player,
            "pressure_legal_balls": s["pressure_legal"],
            "normal_legal_balls": s["normal_legal"],
            "pressure_economy": round(pressure_economy, 2),
            "normal_economy": round(normal_economy, 2),
            "economy_improvement": round(
                normal_economy - pressure_economy, 2
            ),
            "pressure_wickets": s["pressure_wickets"],
            "normal_wickets": s["normal_wickets"],
            "pressure_dots": s["pressure_dots"],
            "normal_dots": s["normal_dots"],
            "pressure_dot_pct": round(pressure_dot_pct, 2),
            "normal_dot_pct": round(normal_dot_pct, 2)
        })

    bowling_results.sort(
        key=lambda x: x["economy_improvement"],
        reverse=True
    )

    # ---------------------------------
    # SAVE CSV FILES
    # ---------------------------------

    OUTPUT.mkdir(parents=True, exist_ok=True)

    def save_results(filename, results):

        if not results:
            print(f"No results to save: {filename}")
            return

        with open(
            OUTPUT / filename,
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=results[0].keys()
            )

            writer.writeheader()
            writer.writerows(results)

    save_results("batter_pressure_rankings.csv", batting_results)
    save_results("bowler_pressure_rankings.csv", bowling_results)

    # ---------------------------------
    # DISPLAY RESULTS
    # ---------------------------------

    print("\n========== CLUTCHIQ ANALYTICS ==========")

    print("Chase deliveries processed:", processed)

    print("\nTOP BATTERS (PROVISIONAL)")

    for i, player in enumerate(batting_results[:10], 1):

        print(
            i,
            player["player"],
            "| Pressure SR:", player["pressure_strike_rate"],
            "| Normal SR:", player["normal_strike_rate"],
            "| Difference:", player["strike_rate_difference"]
        )

    print("\nTOP BOWLERS (PROVISIONAL)")

    for i, player in enumerate(bowling_results[:10], 1):

        print(
            i,
            player["player"],
            "| Pressure economy:", player["pressure_economy"],
            "| Normal economy:", player["normal_economy"],
            "| Improvement:", player["economy_improvement"]
        )

    print("\nSaved ranking files in data/processed/")


if __name__ == "__main__":
    calculate()
