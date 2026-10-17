import pandas as pd

# CSV einlesen
df = pd.read_csv("matching.csv")

# Alle gematchten Repositories sammeln
matched_repos = set(
    pd.concat([
        df["matched_control_1"],
        df["matched_control_2"],
        df["matched_control_3"]
    ])
    .dropna()
    .astype(str)
)

# Zeilen auswählen, deren repo_name in den Match-Spalten vorkommt
result = df[df["repo_name"].isin(matched_repos)]

print(f"Anzahl gefundener Repositories: {len(result)}")
print(result["repo_name"].sort_values().to_string(index=False))

result.to_csv("names_of_matched_repositories.csv", index=False)