#!/usr/bin/env python3
"""
Filter Claude/Agent repositories by activity using SEART export.

This script:
1. Loads the SEART export CSV (active repositories)
2. Loads your Claude/Agent repositories CSV
3. Finds the intersection between both datasets
4. Removes duplicates
5. Saves the filtered repositories to a new CSV

Usage:
    python match_repos_SEART.py \
        --active active_repos.csv \
        --claude repos.csv \
        --output filtered_active_claude_repos.csv
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd


def detect_repo_column(df: pd.DataFrame, filename: str) -> str:
    """
    Automatically detect the repository name column.
    """
    possible_columns = [
        "repo_name",
        "full_name",
        "name",
        "repository",
        "repo",
    ]

    for col in possible_columns:
        if col in df.columns:
            logging.info(f"[{filename}] Using repository column: {col}")
            return col

    logging.error(f"Could not detect repository column in {filename}")
    logging.error(f"Available columns: {list(df.columns)}")
    sys.exit(1)


def load_csv_optimized(path: str) -> pd.DataFrame:
    """
    Load CSV with memory optimization.
    """
    logging.info(f"Loading {path} ...")

    try:
        df = pd.read_csv(
            path,
            low_memory=False,
        )

        logging.info(f"Loaded {len(df):,} rows from {path}")
        return df

    except Exception as e:
        logging.error(f"Failed to load {path}: {e}")
        sys.exit(1)


def normalize_repo_names(series: pd.Series) -> pd.Series:
    """
    Normalize repository names for safer matching.
    """
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
    )


def main():
    parser = argparse.ArgumentParser(
        description="Filter Claude repositories using SEART active repositories export."
    )

    parser.add_argument(
        "--active",
        required=True,
        help="Path to SEART active repositories CSV",
    )

    parser.add_argument(
        "--claude",
        required=True,
        help="Path to Claude repositories CSV",
    )

    parser.add_argument(
        "--output",
        default="filtered_active_claude_repos.csv",
        help="Output CSV path",
    )

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # ------------------------------------------------------------
    # Load datasets
    # ------------------------------------------------------------

    active_df = load_csv_optimized(args.active)
    claude_df = load_csv_optimized(args.claude)

    # ------------------------------------------------------------
    # Detect repository columns
    # ------------------------------------------------------------

    active_repo_col = detect_repo_column(active_df, args.active)
    claude_repo_col = detect_repo_column(claude_df, args.claude)

    # ------------------------------------------------------------
    # Normalize repository names
    # ------------------------------------------------------------

    active_df["_repo_norm"] = normalize_repo_names(active_df[active_repo_col])
    claude_df["_repo_norm"] = normalize_repo_names(claude_df[claude_repo_col])

    # ------------------------------------------------------------
    # Remove duplicates
    # ------------------------------------------------------------

    active_df = active_df.drop_duplicates(subset="_repo_norm")
    claude_df = claude_df.drop_duplicates(subset="_repo_norm")

    logging.info(f"Unique active repos: {len(active_df):,}")
    logging.info(f"Unique Claude repos: {len(claude_df):,}")

    # ------------------------------------------------------------
    # Compute intersection
    # ------------------------------------------------------------

    active_repo_set = set(active_df["_repo_norm"])

    filtered_df = claude_df[
        claude_df["_repo_norm"].isin(active_repo_set)
    ].copy()

    # Remove helper column
    filtered_df = filtered_df.drop(columns=["_repo_norm"])

    # ------------------------------------------------------------
    # Save results
    # ------------------------------------------------------------

    output_path = Path(args.output)

    filtered_df.to_csv(output_path, index=False)

    logging.info("=" * 60)
    logging.info(f"FINAL FILTERED REPOSITORIES: {len(filtered_df):,}")
    logging.info(f"Saved output to: {output_path}")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()