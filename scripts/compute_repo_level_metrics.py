#!/usr/bin/env python3
"""
Compute repository-level metrics for claude adoption.

This script computes:
1. Number of claude file changing commits per repository
2. Percentage of claude adoptor commits per repository

claude adoptor commits are defined as commits authored by developers
who have at least one claude-file changing commit.
"""

import logging
import sys
from typing import Any, Dict, Set, Tuple

import pandas as pd


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all required data files."""
    logging.info("Loading data files...")
    repos_df = pd.read_csv("repos.csv")
    logging.info("Loaded %d repositories", len(repos_df))

    contributors_df = pd.read_csv("ts_contributors_monthly.csv")
    logging.info("Loaded %d contributor records", len(contributors_df))

    claude_commits_df = pd.read_csv("claude_commits.csv")
    logging.info("Loaded %d claude commits", len(claude_commits_df))

    return repos_df, contributors_df, claude_commits_df


def filter_repos_by_stars(repos_df: pd.DataFrame, min_stars: int = 10) -> Set[str]:
    """Filter repositories with at least min_stars GitHub stars."""
    filtered_repos = set(repos_df[repos_df["repo_stars"] >= min_stars]["repo_name"])
    logging.info(
        "Found %d repositories with >= %d stars", len(filtered_repos), min_stars
    )
    return filtered_repos


def get_claude_developers(claude_commits_df: pd.DataFrame) -> Dict[str, Set[str]]:
    """Get developers who have made claude-file changing commits per repo."""
    logging.info("Identifying claude developers...")
    claude_devs = {}
    for _, row in claude_commits_df.iterrows():
        repo = row["repo_name"]
        author = row["author"]

        if repo not in claude_devs:
            claude_devs[repo] = set()
        claude_devs[repo].add(author)

    repos_with_claude = len(claude_devs)
    total_claude_devs = sum(len(devs) for devs in claude_devs.values())
    logging.info(
        "Found %d repositories with claude commits and %d unique claude developers",
        repos_with_claude,
        total_claude_devs,
    )
    return claude_devs


def compute_first_claude_commit_times(
    claude_commits_df: pd.DataFrame,
) -> Dict[str, str]:
    """Compute first claude commit authored_at timestamp per repository."""
    logging.info("Computing first claude commit times...")

    if claude_commits_df.empty:
        return {}

    if "repo_name" not in claude_commits_df or "authored_at" not in claude_commits_df:
        logging.warning("claude_commits_df missing required columns")
        return {}

    first_times_series = claude_commits_df.groupby("repo_name")["authored_at"].min()
    first_times: Dict[str, str] = first_times_series.to_dict()

    logging.info(
        "Computed first claude commit times for %d repositories", len(first_times)
    )
    return first_times


def count_commits_per_developer(
    contributors_df: pd.DataFrame,
) -> Dict[str, Dict[str, int]]:
    """Count total commits per developer per repository."""
    logging.info("Aggregating commits per developer...")
    commits_by_repo_dev = {}

    for _, row in contributors_df.iterrows():
        repo = row["repo_name"]
        author = row["author"]
        commits = row["commits"]

        if repo not in commits_by_repo_dev:
            commits_by_repo_dev[repo] = {}

        if author not in commits_by_repo_dev[repo]:
            commits_by_repo_dev[repo][author] = 0

        commits_by_repo_dev[repo][author] += commits

    total_repos_with_commits = len(commits_by_repo_dev)
    logging.info("Aggregated commits for %d repositories", total_repos_with_commits)
    return commits_by_repo_dev


def compute_claude_metrics(
    repos_with_min_stars: Set[str],
    claude_commits_df: pd.DataFrame,
    claude_developers: Dict[str, Set[str]],
    commits_by_repo_dev: Dict[str, Dict[str, int]],
    first_claude_commit_times: Dict[str, str],
) -> Dict[str, Dict[str, Any]]:
    """Compute claude adoption metrics for each repository."""
    logging.info("Computing claude adoption metrics...")
    results = {}

    for repo in repos_with_min_stars:
        # Count claude file changing commits
        claude_commits_count = len(
            claude_commits_df[claude_commits_df["repo_name"] == repo]
        )

        # Get claude developers for this repo
        repo_claude_devs = claude_developers.get(repo, set())

        # Get all commits for this repo
        repo_commits = commits_by_repo_dev.get(repo, {})

        if not repo_commits:
            claude_adoptor_percentage = 0.0
        else:
            # Count commits from claude adoptor developers
            claude_adoptor_commits = sum(
                commits
                for dev, commits in repo_commits.items()
                if dev in repo_claude_devs
            )

            # Total commits in the repo
            total_commits = sum(repo_commits.values())

            # Calculate percentage
            claude_adoptor_percentage = (
                (claude_adoptor_commits / total_commits) * 100
                if total_commits > 0
                else 0.0
            )

        adoption_time = first_claude_commit_times.get(repo, "")

        results[repo] = {
            "claude_commits": claude_commits_count,
            "claude_adoptor_percentage": claude_adoptor_percentage,
            "claude_adoption_time": adoption_time,
        }

    repos_with_claude_commits = sum(
        1 for r in results.values() if r["claude_commits"] > 0
    )
    logging.info(
        "Computed metrics for %d repositories (%d with claude commits)",
        len(results),
        repos_with_claude_commits,
    )
    return results


def save_results(results: Dict[str, Dict[str, Any]], output_file: str) -> None:
    """Save results to CSV file."""
    logging.info("Saving results to %s", output_file)
    data = []
    for repo, metrics in results.items():
        data.append(
            {
                "repo_name": repo,
                "claude_commits": metrics["claude_commits"],
                "claude_adoptor_percentage": metrics["claude_adoptor_percentage"],
                "claude_adoption_time": metrics["claude_adoption_time"],
            }
        )

    results_df = pd.DataFrame(data)
    results_df = results_df.sort_values("claude_adoptor_percentage", ascending=False)
    results_df.to_csv(output_file, index=False)

    logging.info("Results saved to %s", output_file)
    logging.info("Processed %d repositories", len(results))
    logging.info("Top 10 repositories by claude adoptor percentage:")
    for _, row in results_df.head(10).iterrows():
        logging.info(
            "  %s: %.1f%% (%d commits)",
            row["repo_name"],
            row["claude_adoptor_percentage"],
            row["claude_commits"],
        )


def main() -> None:
    """Main function to compute repository-level claude metrics."""
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.info("Starting repository-level claude metrics computation")

    try:
        repos_df, contributors_df, claude_commits_df = load_data()

        # Filter repos with at least 10 stars
        repos_with_min_stars = filter_repos_by_stars(repos_df, min_stars=10)

        # Get claude developers
        claude_developers = get_claude_developers(claude_commits_df)

        # Count commits per developer
        commits_by_repo_dev = count_commits_per_developer(contributors_df)

        # Compute first claude commit times per repo
        first_claude_commit_times = compute_first_claude_commit_times(claude_commits_df)

        # Compute metrics
        results = compute_claude_metrics(
            repos_with_min_stars,
            claude_commits_df,
            claude_developers,
            commits_by_repo_dev,
            first_claude_commit_times,
        )

        # Save results
        save_results(results, "data/repo_metrics.csv")

        logging.info(
            "Repository-level claude metrics computation completed successfully"
        )

    except Exception as e:
        logging.error("Failed to compute repository metrics: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()