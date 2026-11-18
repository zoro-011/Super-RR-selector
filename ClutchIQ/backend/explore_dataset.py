
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

print("\n========== CLUTCHIQ DATA SUMMARY ==========\n")

for file in sorted(DATA_DIR.glob("*.csv")):
    try:
        df = pd.read_csv(file)

        print(f"\nFILE: {file.name}")
        print(f"ROWS: {len(df)}")
        print(f"COLUMNS: {len(df.columns)}")
        print("COLUMN NAMES:")

        for column in df.columns:
            print(f"  - {column}")

    except Exception as error:
        print(f"ERROR in {file.name}: {error}")

print("\n========== ANALYSIS COMPLETE ==========")
