"""
Standalone script to add high_confidence and other_agents columns to panel_event_monthly.csv

This script:
1. Reads panel_event_monthly.csv
2. Processes claude files and git commits to create commit_months_flat_set data
3. Processes repositories to find dot files and create dot_components_set data
4. Adds high_confidence column based on claude file commit months
5. Adds other_agents column based on dot file components
6. Outputs panel_event_monthly_modified.csv

Required files and paths:
- panel_event_monthly.csv: Input panel data file
- claude_files.csv: Claude files data
- ts_repos_monthly.csv: Treatment analyzed data
- base_repo_path: Path to cloned repositories directory

All functions from claude_rules.ipynb are included in this script.
"""

import pandas as pd
import numpy as np
import subprocess
import os
from pathlib import Path
from collections import Counter


# ============================================================================
# Functions for processing claude files and git commits
# ============================================================================

def get_file_commit_dates_monthly(repo_path, file_path):
    """
    Get all commit months (YYYY-MM) for a specific file in a git repository.

    Args:
        repo_path: Path to the git repository
        file_path: Relative path to the file within the repo

    Returns:
        List of commit months as strings ('YYYY-MM') or None if file not found/error
    """
    try:
        # Ensure the repository directory is marked as safe
        # This is needed for Git 2.35.1+ security feature
        # This is only needed if the repositories are not owned by the user running the script
        subprocess.run(
            ['git', 'config', '--global', '--add', 'safe.directory', repo_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Use git log to get the commit dates for the file
        result = subprocess.run(
            ['git', 'log', '--format=%ai', '--', file_path],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            date_strings = result.stdout.strip().split('\n')
            months = [date_str[:7] for date_str in date_strings if date_str]  # 'YYYY-MM'
            return months
        return None
    except Exception as e:
        print(f"Error processing {repo_path}/{file_path}: {e}")
        return None


def add_commit_months_column(df, base_repo_path):
    """
    Add columns with commit month information (YYYY-MM as string) to the dataframe.

    Args:
        df: DataFrame with 'repo_name' and 'file_path' columns
        base_repo_path: Base path where repos are cloned

    Returns:
        DataFrame with additional columns:
        - commit_months: list of all commit months for the file
        - first_commit_month: earliest (oldest) commit month
        - last_commit_month: most recent commit month
        - num_commits: number of commits affecting the file
    """
    commit_months_list = []
    first_commit_month_list = []
    last_commit_month_list = []
    num_commits_list = []

    for idx, row in df.iterrows():
        repo_name = row['repo_name']
        file_path = row['file_path']

        repo_dir = repo_name.replace('/', '_')
        repo_path = os.path.join(base_repo_path, repo_dir)

        if not os.path.exists(repo_path):
            print(f"Repository not found: {repo_path}")
            commit_months_list.append(None)
            first_commit_month_list.append(None)
            last_commit_month_list.append(None)
            num_commits_list.append(0)
            continue

        months = get_file_commit_dates_monthly(repo_path, file_path)

        if months and len(months) > 0:
            commit_months_list.append(months)
            last_commit_month_list.append(months[0])  # Most recent commit month
            first_commit_month_list.append(months[-1])  # Oldest commit month
            num_commits_list.append(len(months))
        else:
            commit_months_list.append(None)
            first_commit_month_list.append(None)
            last_commit_month_list.append(None)
            num_commits_list.append(0)

        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1}/{len(df)} files...")

    df_copy = df.copy()
    df_copy['commit_months'] = commit_months_list
    df_copy['first_commit_month'] = first_commit_month_list
    df_copy['last_commit_month'] = last_commit_month_list
    df_copy['num_commits'] = num_commits_list

    return df_copy


def flatten_commit_months(x, idx=None):
    """Safely flatten nested list of commit months and report issues"""
    if x is None:
        return []
    if not isinstance(x, list):
        return []
    try:
        result = [month for sublist in x for month in sublist]
        return result
    except (TypeError, AttributeError) as e:
        return []


def analyze_claude_adoption(group):
    """
    Analyze claude adoption patterns for a repository group.
    
    Args:
        group: DataFrame group by repo_name
        
    Returns:
        Series with claude_months, claude_adoption, claude_switch
    """
    # Filter rows where claude is True
    claude_true_rows = group[group['claude'] == True]
    
    # All months where claude is True
    claude_months = claude_true_rows['month'].tolist() if len(claude_true_rows) > 0 else []
    
    # First month where claude is True (adoption month)
    claude_adoption = claude_true_rows['month'].min() if len(claude_true_rows) > 0 else None
    
    # Find switch months (False -> True transitions)
    switch_months = []
    group_reset = group.reset_index(drop=True)
    
    for i in range(len(group_reset)):
        current_claude = group_reset.loc[i, 'claude']
        
        # Check if current is True
        if current_claude == True:
            # Check if previous was False (or this is the first row and it's True)
            if i == 0:
                # First month in data and it's True - this is adoption/switch
                switch_months.append(group_reset.loc[i, 'month'])
            elif group_reset.loc[i-1, 'claude'] == False:
                # Previous was False, current is True - this is a switch
                switch_months.append(group_reset.loc[i, 'month'])
    
    return pd.Series({
        'claude_months': claude_months,
        'claude_adoption': claude_adoption,
        'claude_switch': switch_months
    })


# ============================================================================
# Functions for processing dot files
# ============================================================================

def find_dot_files_and_folders(repo_path):
    """
    Find all files and folders with names starting with '.' in a repository.
    This includes files/folders where the name itself starts with '.' or any ancestor
    directory name starts with '.'.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        tuple: (list of file names, list of file paths, list of dot components)
    """
    dot_files = []
    dot_file_paths = []
    dot_components = []
    
    if not os.path.exists(repo_path):
        return dot_files, dot_file_paths, dot_components
    
    try:
        for root, dirs, files in os.walk(repo_path):
            # Check if current directory or any ancestor starts with '.'
            path_parts = Path(root).parts
            has_dot_ancestor = any(part.startswith('.') for part in path_parts)
            
            # Find which component has the dot
            dot_component = None
            if has_dot_ancestor:
                for part in path_parts:
                    if part.startswith('.'):
                        dot_component = part
                        break
            
            # Add files in current directory
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)
                
                # Check if file name starts with '.' or has dot ancestor
                if file.startswith('.') or has_dot_ancestor:
                    dot_files.append(file)
                    dot_file_paths.append(relative_path)
                    
                    # Determine the dot component
                    if file.startswith('.'):
                        dot_components.append(file)  # The file itself is the dot component
                    else:
                        dot_components.append(dot_component)  # The ancestor directory
            
            # Add directories that start with '.'
            for dir_name in dirs:
                if dir_name.startswith('.'):
                    dir_path = os.path.join(root, dir_name)
                    relative_path = os.path.relpath(dir_path, repo_path)
                    dot_files.append(dir_name)
                    dot_file_paths.append(relative_path)
                    dot_components.append(dir_name)  # The directory itself is the dot component
    
    except Exception as e:
        print(f"Error processing {repo_path}: {e}")
    
    return dot_files, dot_file_paths, dot_components


def add_dot_files_columns(df, base_repo_path):
    """
    Add columns with dot files information to the dataframe.
    
    Args:
        df: DataFrame with 'repo_name' column
        base_repo_path: Base path where repos are cloned
        
    Returns:
        DataFrame with additional columns:
        - dot_files: list of all file/folder names starting with '.'
        - dot_file_paths: list of all file/folder paths starting with '.'
        - dot_components: list of the dot components (file/dir names that start with '.')
    """
    dot_files_list = []
    dot_file_paths_list = []
    dot_components_list = []
    
    counter = 0
    for idx, row in df.iterrows():
        counter += 1
        repo_name = row['repo_name']
        
        # Convert repo_name to directory name (replace '/' with '_')
        repo_dir = repo_name.replace('/', '_')
        repo_path = os.path.join(base_repo_path, repo_dir)
        
        if not os.path.exists(repo_path):
            print(f"Repository not found at counter {counter} (index {idx}): {repo_path}")
            dot_files_list.append([])
            dot_file_paths_list.append([])
            dot_components_list.append([])
            continue
        
        try:
            dot_files, dot_file_paths, dot_components = find_dot_files_and_folders(repo_path)
            dot_files_list.append(dot_files)
            dot_file_paths_list.append(dot_file_paths)
            dot_components_list.append(dot_components)
        except Exception as e:
            print(f"Error processing repository at counter {counter} (index {idx}) ({repo_name}): {e}")
            dot_files_list.append([])
            dot_file_paths_list.append([])
            dot_components_list.append([])
        
        if counter % 50 == 0:
            print(f"Processed {counter}/{len(df)} repositories...")
    
    df_copy = df.copy()
    df_copy['dot_files'] = dot_files_list
    df_copy['dot_file_paths'] = dot_file_paths_list
    df_copy['dot_components'] = dot_components_list
    
    return df_copy


# ============================================================================
# Functions for adding columns to panel data
# ============================================================================

def check_high_confidence(row, rules_dict):
    """
    Check if a row has high confidence based on claude file commit months.
    
    Logic:
    - If dataset_source == 'control' → NA
    - If time_to_event < 0 → NA
    - If time_to_event == 0 → True (adoption month)
    - If time_to_event > 0 → Check if time is in commit_months_flat_set
    """
    # Case 1: control group → NA
    if row.get('dataset_source') == 'control':
        return np.nan
    
    # is_treatment cases:
    time_to_event = row['time_to_event']
    
    # Case 2: time_to_event is negative → NA
    if time_to_event < 0:
        return np.nan
    
    # Case 3: time_to_event == 0 → True (adoption month)
    if time_to_event == 0:
        return True
    
    # Case 4: time_to_event > 0 → Check if time is in commit_months_flat_set
    repo_name = row['repo_name']
    time = row['time']
    
    # Check if repo exists in rules_dict
    if repo_name in rules_dict:
        # Check if time is in commit_months_flat_set
        # Match notebook exactly - no type conversion, no extra checks
        if time in rules_dict[repo_name]:
            return True  # TRUE - time is in commits
        else:
            return False  # FALSE - in rules but time not in commits
    else:
        return False  # FALSE - repo not in rules


def determine_other_agents(row, repo_to_has_other_agents):
    """
    Determine if a repo has other agents based on dot file components.
    
    Logic:
    - If dataset_source == 'control' → NA
    - If dataset_source == 'treatment' and time_to_event < 0 → NA
    - If dataset_source == 'treatment' and time_to_event >= 0 → Check for other agents
    """
    # If data_source is control, return NA
    if row['dataset_source'] == 'control':
        return np.nan
    
    # If treatment and time_to_event < 0, return NA
    # Note: This matches the notebook - it doesn't explicitly check for NaN
    if row['dataset_source'] == 'treatment' and row['time_to_event'] < 0:
        return np.nan
    
    # If treatment and time_to_event >= 0, check for other agents
    if row['dataset_source'] == 'treatment' and row['time_to_event'] >= 0:
        repo_name = row['repo_name']
        return repo_to_has_other_agents.get(repo_name, False)
    
    # Default case (shouldn't reach here)
    return False


# ============================================================================
# Main processing functions
# ============================================================================

def create_rules_dataframe(claude_files_path, ts_repos_monthly_path, base_repo_path):
    """
    Create df_rules dataframe with commit_months_flat_set from claude files data.
    
    Args:
        claude_files_path: Path to claude_files.csv
        ts_repos_monthly_path: Path to ts_repos_monthly.csv
        base_repo_path: Base path where repos are cloned
        
    Returns:
        DataFrame with repo_name and commit_months_flat_set columns
    """
    print("Loading claude files data...")
    df_claude_info = pd.read_csv(claude_files_path)
    
    print("Loading treatment analyzed data...")
    df_treatment_analyzed = pd.read_csv(ts_repos_monthly_path)
    
    # Filter claude info to only repos in treatment analyzed
    df_claude_info_interested = df_claude_info[
        df_claude_info["repo_name"].isin(df_treatment_analyzed["repo_name"])
    ].reset_index(drop=True)
    
    print(f"Processing {len(df_claude_info_interested)} claude files...")
    # Add commit months
    df_with_months = add_commit_months_column(df_claude_info_interested, base_repo_path)
    
    # Group by repo_name and aggregate
    df_aggregated = df_with_months.groupby('repo_name').agg({
        'file_path': list,
        'file_url': list,
        'commit_months': list,
        'first_commit_month': list,
        'last_commit_month': list,
        'num_commits': list
    }).reset_index()
    
    # Analyze claude adoption
    df_sorted = df_treatment_analyzed.sort_values(['repo_name', 'month']).copy()
    df_claude_adoption = df_sorted.groupby('repo_name').apply(
        analyze_claude_adoption, include_groups=False
    ).reset_index()
    
    # Merge
    df_rules = df_aggregated.merge(df_claude_adoption, on='repo_name', how='inner')
    
    # Flatten commit months
    flattened_months = []
    for idx, row in df_rules.iterrows():
        result = flatten_commit_months(row['commit_months'], idx)
        flattened_months.append(result)
    
    df_rules['commit_months_flat'] = flattened_months
    
    # Filter by claude_adoption date
    df_rules = df_rules[
        (df_rules['claude_adoption'] >= '2025-05') & 
        (df_rules['claude_adoption'] < '2026-05')
    ].copy()
    
    # Create commit_months_flat_set
    # Match notebook exactly
    df_rules['commit_months_flat_set'] = df_rules['commit_months_flat'].apply(
        lambda x: list(set(x)) if isinstance(x, list) else []
    )
    
    return df_rules[['repo_name', 'commit_months_flat_set']]


def create_dot_files_dataframe(df_rules, base_repo_path):
    """
    Create df_with_dot_files dataframe with dot_components_set from repositories.
    
    Args:
        df_rules: DataFrame with repo_name column
        base_repo_path: Base path where repos are cloned
        
    Returns:
        DataFrame with repo_name and dot_components_set columns
    """
    print("Processing repositories for dot files...")
    df_with_dot_files = add_dot_files_columns(df_rules, base_repo_path)
    
    # Create dot_components_set
    df_with_dot_files['dot_components_set'] = df_with_dot_files['dot_components'].apply(
        lambda x: list(set(x)) if isinstance(x, list) else []
    )
    
    return df_with_dot_files[['repo_name', 'dot_components_set']]


def find_claude_files_in_repo(repo_path):
    """
    Find claude files in a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        List of claude file paths
    """
    claude_files = []
    claude_patterns = ['.CLAUDE.md']
    
    if not os.path.exists(repo_path):
        return claude_files
    
    try:
        for root, dirs, files in os.walk(repo_path):
            # Check files
            for file in files:
                filename = file.lower()
                if filename == "claude.md" :
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, repo_path)
                    claude_files.append(relative_path)
            
            # Check for .claude directory
            if '.claude' in dirs:
                claude_dir = os.path.join(root, '.claude')
                for subroot, subdirs, subfiles in os.walk(claude_dir):
                    for subfile in subfiles:
                            file_path = os.path.join(subroot, subfile)
                            relative_path = os.path.relpath(file_path, repo_path)
                            claude_files.append(relative_path)
    except Exception as e:
        print(f"Error finding claude files in {repo_path}: {e}")
    
    return claude_files


def create_rules_from_panel(df_panel, base_repo_path):
    """
    Create rules dataframe from panel data by processing repos directly.
    
    Args:
        df_panel: Panel dataframe
        base_repo_path: Base path where repos are cloned
        
    Returns:
        DataFrame with repo_name and commit_months_flat_set columns
    """
    unique_repos = df_panel['repo_name'].unique()
    rules_data = []
    
    for repo_name in unique_repos:
        repo_dir = repo_name.replace('/', '_')
        repo_path = os.path.join(base_repo_path, repo_dir)
        
        if not os.path.exists(repo_path):
            continue
        
        # Find claude files in repo
        claude_files = find_claude_files_in_repo(repo_path)
        
        if not claude_files:
            continue
        
        # Get commit months for all claude files
        all_commit_months = []
        for file_path in claude_files:
            months = get_file_commit_dates_monthly(repo_path, file_path)
            if months:
                all_commit_months.extend(months)
        
        if all_commit_months:
            commit_months_set = list(set(all_commit_months))
            rules_data.append({
                'repo_name': repo_name,
                'commit_months_flat_set': commit_months_set
            })
    
    return pd.DataFrame(rules_data)


def main():
    """Main function to process panel_event_monthly.csv and add columns."""
    
    # File paths - adjust these paths as needed
    input_file = '../data/panel_event_monthly.csv'
    output_file = '../data/panel_event_monthly_modified.csv'
    
    # Required paths - these must exist
    claude_files_path = '../data/claude_files.csv'
    ts_repos_monthly_path = '../data/ts_repos_monthly.csv'
    base_repo_path = "/home/dstrell/raid/sonar-project/ClaudeRepos"    
    print("="*80)
    print("Processing panel_event_monthly.csv to add confidence and agent columns")
    print("="*80)
    
    # Validate required files exist
    print("\nValidating required files and paths...")
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    if not os.path.exists(claude_files_path):
        raise FileNotFoundError(f"Required file not found: {claude_files_path}")
    if not os.path.exists(ts_repos_monthly_path):
        raise FileNotFoundError(f"Required file not found: {ts_repos_monthly_path}")
    if not os.path.exists(base_repo_path):
        raise FileNotFoundError(f"Required repository path not found: {base_repo_path}")
    print("All required files and paths found.")
    
    # Read panel data
    print(f"\nReading {input_file}...")
    df_panel = pd.read_csv(input_file, low_memory=False)
    print(f"Loaded {len(df_panel)} rows from {input_file}")
    
    # Get unique repos from panel data
    unique_repos = df_panel['repo_name'].unique()
    print(f"Found {len(unique_repos)} unique repositories in panel data")
    
    # Create rules dataframe
    print("\n" + "="*80)
    print("Step 1: Creating claude rules data (commit_months_flat_set)")
    print("="*80)
    
    print("Using claude_files.csv and ts_repos_monthly.csv...")
    df_rules = create_rules_dataframe(claude_files_path, ts_repos_monthly_path, base_repo_path)
    print(f"Created rules data for {len(df_rules)} repositories")
    
    # Create dot files dataframe
    print("\n" + "="*80)
    print("Step 2: Creating dot files data (dot_components_set)")
    print("="*80)
    
    # Use df_rules for dot files processing
    df_repos_for_dot_files = df_rules[['repo_name']].copy()
    df_with_dot_files = create_dot_files_dataframe(df_repos_for_dot_files, base_repo_path)
    print(f"Created dot files data for {len(df_with_dot_files)} repositories")
    
    # Create dictionaries for fast lookup
    print("\n" + "="*80)
    print("Step 3: Creating lookup dictionaries")
    print("="*80)
    
    # Match notebook: use set_index and to_dict to create rules_dict with lists
    rules_dict = df_rules.set_index('repo_name')['commit_months_flat_set'].to_dict()
    
    # Define other agent components
    other_agent_components = {
        'copilot-instructions.md',
        '.cursor', '.cursorrules', '.cursorignore',
    }
    
    repo_to_has_other_agents = {}
    for _, row in df_with_dot_files.iterrows():
        repo_name = row['repo_name']
        components = set(row['dot_components_set']) if row['dot_components_set'] else set()
        repo_to_has_other_agents[repo_name] = bool(components.intersection(other_agent_components))
    
    print(f"Created lookup for {len(rules_dict)} repositories (rules)")
    print(f"Created lookup for {len(repo_to_has_other_agents)} repositories (dot files)")
    
    # Add columns to panel
    print("\n" + "="*80)
    print("Step 4: Adding columns to panel data")
    print("="*80)
    
    print("Adding high_confidence column...")
    df_panel['high_confidence'] = df_panel.apply(
        lambda row: check_high_confidence(row, rules_dict), 
        axis=1
    )
    
    print("Adding other_agents column...")
    df_panel['other_agents'] = df_panel.apply(
        lambda row: determine_other_agents(row, repo_to_has_other_agents),
        axis=1
    )
    
    # Print summary statistics
    print("\n" + "="*80)
    print("Summary Statistics")
    print("="*80)
    
    print("\nHigh confidence distribution:")
    print(df_panel['high_confidence'].value_counts(dropna=False))
    
    print("\nOther agents distribution:")
    print(df_panel['other_agents'].value_counts(dropna=False))
    
    print("\nBreakdown by dataset_source:")
    print("\nHigh confidence by dataset_source:")
    print(df_panel.groupby('dataset_source')['high_confidence'].value_counts(dropna=False))
    print("\nOther agents by dataset_source:")
    print(df_panel.groupby('dataset_source')['other_agents'].value_counts(dropna=False))
    
    # Save output
    print(f"\n" + "="*80)
    print(f"Saving output to {output_file}...")
    df_panel.to_csv(output_file, index=False)
    print(f"Successfully saved {len(df_panel)} rows to {output_file}")
    
    print("\nDone!")


if __name__ == '__main__':
    main()