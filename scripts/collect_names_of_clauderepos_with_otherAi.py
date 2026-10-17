#!/usr/bin/env python3
"""
Collect repo_name values from copilot_commits.csv and cursor_commits.csv,
remove duplicates, and save them to claudeReposWithoutOtherAi.csv.

Usage (from the script/ folder):
    python collect_other_ai_repos.py
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
INPUT_FILES = [
    DATA_DIR / "copilot_commits.csv",
    DATA_DIR / "cursor_commits.csv",
]
OUTPUT_FILE = DATA_DIR / "claudeReposWithoutOtherAi.csv"


def load_repo_names(path: Path) -> pd.Series:
    """Read the repo_name column from a CSV file."""
    if not path.exists():
        print(f"[warning] {path.name} not found, skipping")
        return pd.Series(dtype=str)

    df = pd.read_csv(path)
    if "repo_name" not in df.columns:
        print(f"[warning] {path.name} has no 'repo_name' column, skipping")
        return pd.Series(dtype=str)

    repos = df["repo_name"].dropna().astype(str).str.strip()
    repos = repos[repos != ""].drop_duplicates()
    print(f"{path.name}: {len(repos)} repositories")
    return repos


def main() -> None:
    all_repos = pd.concat([load_repo_names(p) for p in INPUT_FILES], ignore_index=True)
    unique_repos = sorted(all_repos.drop_duplicates())

    pd.DataFrame({"repo_name": unique_repos}).to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(unique_repos)} unique repositories to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()