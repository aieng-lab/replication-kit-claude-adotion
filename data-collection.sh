# scripts to build the monthly time series dataset in order
python -m scripts.clone_repos > logs/clone_repos.log
python -m scripts.analyze_repos_copilot --aggregation=month
python -m scripts.analyze_repos_cursor --aggregation=month
python -m scripts.collect_names_of_clauderepos_with_otherAi
python -m scripts.postfiltering_AIRepos_from_ClaudeRepos
python -m scripts.analyze_repos --aggregation=month
python -m scripts.fetch_gharchive --aggregation=month
python -m scripts.run_sonarqube --aggregation=month



python -m scripts.clone_repos --control 
python -m scripts.get_names_of_matched_control_repos
python -m scripts.analyze_repos --aggregation=month
python -m scripts.analyze_repos_copilot --aggregation=month
python -m scripts.analyze_repos_cursor --aggregation=month
python -m scripts.collect_names_of_controlrepos_with_otherAi
python -m scripts.postfiltering_AIRepos_from_ControlRepos
python -m scripts.analyze_repos_control --aggregation=month
python -m scripts.fetch_gharchive --aggregation=month --control
python -m scripts.run_sonarqube --aggregation=month ---control