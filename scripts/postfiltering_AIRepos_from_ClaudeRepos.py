#!/usr/bin/env python3
"""
Remove all rows from repos.csv whose repo_name appears in
claudeReposWithoutOtherAi.csv and save the result to repos_without_other_ai.csv.

repos.csv itself is not modified.

Usage (from the script/ folder):
    python filter_repos_without_other_ai.py
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
REPOS_CSV = DATA_DIR / "repos.csv"
EXCLUDE_CSV = DATA_DIR / "claudeReposWithoutOtherAi.csv"
OUTPUT_FILE = DATA_DIR / "repos_without_other_ai.csv"


def main() -> None:
    # Read everything as text so all values are written back unchanged
    repos = pd.read_csv(REPOS_CSV, dtype=str, keep_default_na=False)
    exclude = pd.read_csv(EXCLUDE_CSV, dtype=str)["repo_name"].dropna().str.strip()
    exclude_set = set(exclude)

    mask = repos["repo_name"].str.strip().isin(exclude_set)
    result = repos[~mask]

    not_found = exclude_set - set(repos["repo_name"].str.strip())

    print(f"repos.csv:                   {len(repos)} rows")
    print(f"Repositories to exclude:     {len(exclude_set)}")
    print(f"  of which found in repos:   {mask.sum()} rows removed")
    print(f"  not present in repos.csv:  {len(not_found)}")
    print(f"Remaining:                   {len(result)} rows")

    result.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()