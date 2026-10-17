# A Replication Study of Cursor's Velocity--Quality Trade-off: Evidence from Claude Code Adoption in Open-Source Projects

This repository contains the replication package of this paper:


## Organization

* The `scripts/` folder contains all the scripts we used to collect data, run the propensity score matching, and collect metrics through SonarQube and GH Archive.  Rerunning the scripts will likely not get the same dataset we obtained for our paper because of different aspects: GitHub repositories growing and taken down, GitHub API changing, SonarQube changing, etc.
* The `data/` folder contains the dataset we used for our paper.
    * `repos.csv`: Metadata for treatment group repositories (Claude-adopting projects)
    * `claude_commits.csv`: Commit-level data showing commits modifying CLAUDE.md files
    * `claude_files.csv`: File-level data for Claude configuration files
    * `matching.csv`: Propensity score matching results (treatment-control pairs)
    * `panel_event_monthly.csv`: Main panel dataset used for DiD analysis (monthly aggregated)
    * `panel_event_monthly_modified.csv`: The same as panel_event_monthly.csv but includes confidence and agents
    * `ts_repos_monthly.csv` / `ts_repos_control_monthly.csv`: Monthly time series for treatment/control groups
    * `repo_metrics.csv`: Additional repository-level metrics (stars, contributors, etc.)
    * `sonarqube_warnings.csv`: SonarQube static analysis warnings per repository (as available)
    * `sonarqube_warning_definitions.csv`: Definitions and categories of SonarQube warning types
* The `notebooks/` folder contains R notebooks that will read from `data/` and reproduce results in the paper.
    * `DataCollection.md`: Dataset description
    * `PropensityScoreMatching.md`: Matching results
    * `DiffInDiffBorusyak.md`: Main DiD results
    * `DynamicPanel.md`: Main panel GMM results
    * `AnalyzeSonarQubeWarnings.md`: Appendix analysis on SonarQube warnings
    
* The `plots/` folder contains all the plots in this paper (`.gitignore`d in the GitHub repository but available in Zenodo)

## Development Environment

All results were obtained using **R 4.6.1** for statistical analysis and visualization (DiD estimation, panel models, plotting), and **Python 3.12.3** for data collection scripts (GitHub API, BigQuery, SonarQube). We provide the detailed packages and their versions for future replication purposes.
Due to the R ecosystem constantly evolving, different R versions and package versions may lead to slightly different results for this paper.

### R Packages

| Package | Version | Description |
|---------|---------|-------------|
| tidyverse | 2.0.0 | Data manipulation and visualization |
| tidyverse | 2.0.0 | Meta-package for data science workflows |
| ggplot2 | 4.0.3 | Grammar of graphics plotting |
| data.table | 1.18.4 | Fast data manipulation |
| dplyr | 1.2.1 | Data manipulation verbs |
| tidyr | 1.3.2 | Data tidying |
| tibble | 3.3.1 | Modern data frames |
| readr | 2.2.0 | Fast CSV import |
| stringr | 1.6.0 | String manipulation |
| forcats | 1.0.1 | Factor handling |
| lubridate | 1.9.5 | Date/time manipulation |
| scales | 1.4.0 | Scale functions for visualization |
| fixest | 0.14.2 | Fixed effects estimation |
| didimputation | 0.5.1 | Borusyak et al. imputation estimator |
| plm | 2.6-7 | Panel data models (GMM) |
| modelsummary | 2.6.0 | Model summary tables |
| knitr | 1.51 | Dynamic report generation |
| kableExtra | 1.4.1 | Enhanced table formatting |
| gridExtra | 2.3.1 | Arrange multiple plots |
| RColorBrewer | 1.1-3 | Color palettes |
| Cairo | 1.7-0 | High-quality graphics device |
| rmarkdown | 2.31 | R Markdown document rendering |

### Python Packages

| Package | Version | Description |
|---------|---------|-------------|
| pandas | 3.0.3 | Data manipulation |
| numpy | 2.5.0 | Numerical computing |
| GitPython | 3.1.50 | Git repository interaction |
| requests | 2.34.2 | HTTP requests (SonarQube API, npm registry) |
| python-dotenv | 1.2.2 | Environment variable management |
| PyGithub | 2.9.1 | GitHub API client |
| google-cloud-bigquery | 3.42.1 | BigQuery client for GH Archive |
| db-dtypes | 1.7.0 | Pandas data types for BigQuery results |
| pyarrow | 24.0.0 | Data conversion for BigQuery to_dataframe() |
| scikit-learn | 1.9.0 | Machine learning (propensity scores) |
| semver | 3.0.4 | Semantic versioning |
| node-semver | 0.9.1 | Node.js semver parsing |
| gql | 4.4.0 | GraphQL client |
| aiohttp | 3.14.4 | Async HTTP for GraphQL |

## Replication Instructions

### 1. Obtain the Data

Clone this repository


### 2. Set Up R Environment

Install R 4.6.1 and the required packages:

```r
install.packages(c("tidyverse","ggplot2","dplyr","tidyr","tibble","readr","stringr","forcats",
          "lubridate","scales","data.table","didimputation","fixest","plm","modelsummary",
          "knitr","kableExtra","gridExtra","RColorBrewer","Cairo","rmarkdown"))
```

### 3. Reproduce Results

Knit the notebooks in the following order (Using RStudio or the R VS Code extension):

1. **`notebooks/DataCollection.Rmd`** — Overview of the dataset
2. **`notebooks/PropensityScoreMatching.Rmd`** — Matching diagnostics
3. **`notebooks/DiffInDiffBorusyak.Rmd`** — Main DiD results
4. **`notebooks/DynamicPanel.Rmd`** — Panel GMM results
6. **`notebooks/AnalyzeSonarQubeWarnings.Rmd`** — SonarQube analysis

Each notebook reads from `data/` and outputs tables/figures to `plots/`.

### 4. (Optional) Rerun Data Collection

To rerun the data collection scripts (not recommended for exact replication):

```bash
# Set up Python environment
python -m venv venv
source venv/bin/activate
pip install pandas numpy requests python-dotenv GitPython PyGithub google-cloud-bigquery db-dtypes pyarrow scikit-learn semver node-semver gql aiohttp

# Configure API keys in .env file
cp .env.example .env
# Edit .env with your GitHub token and BigQuery credentials

# Run scripts (see scripts/ for individual script usage)
```

**Note:** Data collection scripts interact with live APIs and will produce different results due to repository changes, API updates, or rate limiting.
