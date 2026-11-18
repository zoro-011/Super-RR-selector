
import csv
import html
from pathlib import Path
from collections import Counter

import streamlit as st


# =====================================================
# CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = (
    BASE_DIR / "data" / "processed" / "selected_deliveries.csv"
)

BATTER_FILE = (
    BASE_DIR / "data" / "processed" / "clutchiq_batter_scores.csv"
)

BOWLER_FILE = (
    BASE_DIR / "data" / "processed" / "clutchiq_bowler_scores.csv"
)


st.set_page_config(
    page_title="ClutchIQ | Cricket Intelligence",
    page_icon="🏏",
    layout="wide"
)


# =====================================================
# THEME
# =====================================================

st.markdown("""
<style>

.stApp {
    background: #090d0b;
    color: #f2f5f2;
}

[data-testid="stSidebar"] {
    background: #101713;
}

h1, h2, h3 {
    color: #f2f5f2;
}

.metric-card {
    background: #121b16;
    border: 1px solid #263b2d;
    padding: 20px;
    border-radius: 12px;
}

.brand {
    color: #a3ff68;
    font-weight: 800;
    letter-spacing: 3px;
}

.small-text {
    color: #91a397;
}

[data-testid="stMetricValue"] {
    color: #a3ff68;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# DATA FUNCTIONS
# =====================================================

@st.cache_data
def load_statistics():

    stats = {
        "deliveries": 0,
        "batter_runs": 0,
        "wickets": 0,
        "matches": set(),
        "batters": set(),
        "bowlers": set(),
        "extras": Counter()
    }

    if not DATA_FILE.exists():
        return None

    with open(
        DATA_FILE,
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            stats["deliveries"] += 1

            stats["batter_runs"] += int(
                float(row.get("runs") or 0)
            )

            if row.get("is_wicket", "").strip().lower() == "true":
                stats["wickets"] += 1

            stats["matches"].add(row.get("match_id"))

            if row.get("striker_name"):
                stats["batters"].add(row["striker_name"])

            if row.get("bowler_name"):
                stats["bowlers"].add(row["bowler_name"])

            stats["extras"][
                row.get("extras_type") or "None"
            ] += 1

    stats["matches"] = len(stats["matches"])
    stats["batters"] = len(stats["batters"])
    stats["bowlers"] = len(stats["bowlers"])

    return stats


@st.cache_data
def load_rankings(file_path):

    path = Path(file_path)

    if not path.exists():
        return []

    with open(
        path,
        encoding="utf-8-sig",
        newline=""
    ) as file:

        return list(csv.DictReader(file))


def safe_float(value, default=0.0):

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def show_html_table(headers, rows):

    table_html = """
    <div style="overflow-x:auto;">
    <table style="
        width:100%;
        border-collapse:collapse;
        color:#f2f5f2;
        font-size:14px;
    ">
    <thead>
    <tr style="background:#183b32;">
    """

    for header in headers:
        table_html += (
            f"<th style='padding:12px;text-align:left;'>"
            f"{html.escape(str(header))}</th>"
        )

    table_html += "</tr></thead><tbody>"

    for row in rows:

        table_html += (
            "<tr style='border-bottom:1px solid #263b2d;'>"
        )

        for value in row:

            table_html += (
                "<td style='padding:12px;'>"
                f"{html.escape(str(value))}"
                "</td>"
            )

        table_html += "</tr>"

    table_html += "</tbody></table></div>"

    st.markdown(
        table_html,
        unsafe_allow_html=True
    )


# =====================================================
# HEADER
# =====================================================

st.markdown(
    '<p class="brand">CLUTCHIQ / CRICKET INTELLIGENCE</p>',
    unsafe_allow_html=True
)

st.title("Performance Under Pressure")

st.markdown(
    '<p class="small-text">'
    'Beyond statistics. Measuring performance when it matters.'
    '</p>',
    unsafe_allow_html=True
)

st.divider()


# =====================================================
# NAVIGATION
# =====================================================

page = st.sidebar.radio(
    "NAVIGATION",
    ["Overview", "Batters", "Bowlers", "Methodology"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### CLUTCHIQ")
st.sidebar.caption("SupeRR Selector · Season 2")


# =====================================================
# OVERVIEW
# =====================================================

if page == "Overview":

    st.title("🏏 ClutchIQ")
    st.caption("Cricket Pressure Performance Intelligence")

    data = load_statistics()

    if data is None:
        st.error(
            "Dataset not found. Check data/processed/"
        )
        st.stop()

    # Dataset metrics

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Deliveries Analysed",
        f"{data['deliveries']:,}"
    )

    c2.metric(
        "Batter Runs",
        f"{data['batter_runs']:,}"
    )

    c3.metric(
        "Wicket Events",
        f"{data['wickets']:,}"
    )

    c4, c5, c6 = st.columns(3)

    c4.metric("Matches", f"{data['matches']:,}")
    c5.metric("Batters", f"{data['batters']:,}")
    c6.metric("Bowlers", f"{data['bowlers']:,}")

    st.divider()

    st.subheader("🏆 Top Pressure Performers")

    batter_rows = load_rankings(BATTER_FILE)
    bowler_rows = load_rankings(BOWLER_FILE)

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 🏏 Top Batter")

        if batter_rows:

            batter = batter_rows[0]

            st.metric(
                "Player",
                batter.get("player", "Unknown")
            )

            st.metric(
                "ClutchIQ Score",
                f"{safe_float(batter.get('clutchiq_score')):.2f}"
            )

            st.caption(
                "Pressure Strike Rate: "
                f"{safe_float(batter.get('pressure_strike_rate')):.2f}"
            )

        else:
            st.info("Batter rankings not available.")

    with col2:

        st.markdown("### 🎯 Top Bowler")

        if bowler_rows:

            bowler = bowler_rows[0]

            st.metric(
                "Player",
                bowler.get("player", "Unknown")
            )

            st.metric(
                "ClutchIQ Score",
                f"{safe_float(bowler.get('clutchiq_score')):.2f}"
            )

            st.caption(
                "Pressure Economy: "
                f"{safe_float(bowler.get('pressure_economy')):.2f}"
            )

        else:
            st.info("Bowler rankings not available.")

    st.divider()

    st.subheader("The ClutchIQ Mission")

    st.markdown("""
    ClutchIQ identifies players who perform in high-pressure
    situations across IPL and T20 International cricket.

    **Our focus:**

    - Batting under chase pressure
    - Bowling when the match is on the line
    - Performance compared with normal situations
    - Sample-size-aware player rankings
    """)

    st.warning(
        "Rankings are provisional and require further methodology "
        "and data validation before competition submission."
    )


# =====================================================
# BATTERS
# =====================================================

elif page == "Batters":

    st.title("🏏 ClutchIQ Batter Rankings")

    rows = load_rankings(BATTER_FILE)

    if not rows:
        st.warning("Batter rankings not generated yet.")
        st.stop()

    st.caption(
        "Provisional pressure-performance rankings"
    )

    display_rows = []

    for i, r in enumerate(rows[:10]):

        display_rows.append([
            i + 1,
            r.get("player", ""),
            f"{safe_float(r.get('clutchiq_score')):.2f}",
            f"{safe_float(r.get('pressure_strike_rate')):.2f}",
            f"{safe_float(r.get('normal_strike_rate')):.2f}",
            safe_int(r.get("pressure_runs")),
            safe_int(r.get("pressure_balls")),
            f"{safe_float(r.get('reliability')) * 100:.1f}%"
        ])

    show_html_table(
        [
            "Rank",
            "Batter",
            "ClutchIQ Score",
            "Pressure SR",
            "Normal SR",
            "Pressure Runs",
            "Pressure Balls",
            "Reliability"
        ],
        display_rows
    )

    st.caption(
        "Scores are relative rankings among qualified batters."
    )


# =====================================================
# BOWLERS
# =====================================================

elif page == "Bowlers":

    st.title("🎯 ClutchIQ Bowler Rankings")

    rows = load_rankings(BOWLER_FILE)

    if not rows:
        st.warning("Bowler rankings not generated yet.")
        st.stop()

    st.caption(
        "Provisional chase-pressure rankings"
    )

    display_rows = []

    for i, r in enumerate(rows[:10]):

        display_rows.append([
            i + 1,
            r.get("player", ""),
            f"{safe_float(r.get('clutchiq_score')):.2f}",
            f"{safe_float(r.get('pressure_economy')):.2f}",
            f"{safe_float(r.get('normal_economy')):.2f}",
            safe_int(r.get("pressure_wickets")),
            safe_int(r.get("pressure_legal_balls")),
            f"{safe_float(r.get('reliability')) * 100:.1f}%"
        ])

    show_html_table(
        [
            "Rank",
            "Bowler",
            "ClutchIQ Score",
            "Pressure Economy",
            "Normal Economy",
            "Pressure Wickets",
            "Pressure Balls",
            "Reliability"
        ],
        display_rows
    )

    st.caption(
        "Scores are relative rankings among qualified bowlers."
    )


# =====================================================
# METHODOLOGY
# =====================================================

elif page == "Methodology":

    st.title("ClutchIQ Methodology")

    st.caption(
        "How ClutchIQ measures cricket performance under pressure"
    )

    st.divider()

    # OBJECTIVE

    st.subheader("1. Objective")

    st.write(
        "ClutchIQ identifies batters and bowlers who perform "
        "effectively under pressure using historical IPL and "
        "T20I ball-by-ball data from 2022 onwards."
    )

    # PRESSURE DEFINITION

    st.subheader("2. Pressure Definition")

    st.write(
        "The current model analyses second-innings chases."
    )

    st.markdown("""
    A delivery is classified as pressure-related when either
    condition applies:

    - Required Run Rate (RRR) is 10 or higher.
    - Six or more wickets have been lost and 60 or fewer balls remain.

    Other eligible chase deliveries are classified as normal situations.

    These thresholds are model-defined assumptions.
    """)

    # BATTER SCORING

    st.subheader("3. Batter Scoring Model")

    st.write(
        "Batters are evaluated using three weighted indicators:"
    )

    st.markdown("""
    | Performance Metric | Weight |
    |---|---:|
    | Strike-rate improvement | 50% |
    | Pressure strike rate | 30% |
    | Runs under pressure | 20% |
    """)

    st.markdown(
        "**Minimum qualification:** 30 pressure balls."
    )

    st.latex(
        r"Reliability = \min\left(1,\sqrt{\frac{P}{120}}\right)"
    )

    st.caption("P = Number of pressure balls faced.")

    st.divider()

    # BOWLER SCORING

    st.subheader("4. Bowler Scoring Model")

    st.write(
        "Bowlers are evaluated using three weighted indicators:"
    )

    st.markdown("""
    | Performance Metric | Weight |
    |---|---:|
    | Economy-rate improvement | 40% |
    | Wicket-rate improvement | 30% |
    | Dot-ball-rate improvement | 30% |
    """)

    st.markdown(
        "**Minimum qualification:** 60 legal pressure balls "
        "and 60 legal normal balls."
    )

    st.latex(
        r"Reliability = \min\left(1,"
        r"\sqrt{\frac{\min(P,N)}{120}}\right)"
    )

    st.caption(
        "P = Pressure legal balls; N = Normal legal balls."
    )

    st.divider()

    # FINAL SCORE

    st.subheader("5. Final ClutchIQ Score")

    st.write(
        "Each performance metric is converted into a percentile "
        "relative to qualified players."
    )

    st.latex(
        r"\text{ClutchIQ Score} = "
        r"\text{Weighted Percentile Score} \times \text{Reliability}"
    )

    st.info(
        "Higher scores indicate stronger relative performance "
        "under pressure within the analysed dataset. "
        "Scores are not probabilities."
    )

    st.divider()

    # DATA PROCESSING

    st.subheader("6. Data Processing")

    st.markdown("""
    1. Load historical ball-by-ball data.
    2. Identify second-innings chase deliveries.
    3. Calculate match pressure conditions.
    4. Separate pressure and normal deliveries.
    5. Aggregate batter and bowler statistics.
    6. Apply qualification and reliability requirements.
    7. Generate ranked leaderboards.
    """)

    st.divider()

    # LIMITATIONS

    st.subheader("7. Limitations")

    st.markdown("""
    - The model currently focuses on second-innings chases.
    - Pressure thresholds are model-defined assumptions.
    - Minimum sample requirements reduce but do not eliminate uncertainty.
    - Some extras classifications, particularly 'other' and
      'overstep', remain provisional.
    - Scores are relative rankings, not predictions of future performance.
    """)

    st.warning(
        "ClutchIQ is an analytical performance-ranking system, "
        "not a match-outcome prediction system."
    )

