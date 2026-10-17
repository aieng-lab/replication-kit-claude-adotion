import pandas as pd

# Dateien
MATCHING_FILE = "matching.csv"
NON_AI_FILE = "controlReposWithoutAi.csv"
OUTPUT_FILE = "matching_final.csv"

# CSVs laden
matching = pd.read_csv(MATCHING_FILE)
non_ai = pd.read_csv(NON_AI_FILE)

# Control-Repos, die ausgeschlossen werden sollen
excluded_controls = set(non_ai["repo_name"].astype(str).str.strip())

selected_rows = []

for _, row in matching.iterrows():

    controls = [
        row["matched_control_1"],
        row["matched_control_2"],
        row["matched_control_3"],
    ]

    # Hatte die Zeile ursprünglich überhaupt einen Match?
    had_match = any(
        pd.notna(c) and str(c).strip() != ""
        for c in controls
    )

    chosen = None

    # Ersten zulässigen Match auswählen
    for control in controls:
        if (
            pd.notna(control)
            and str(control).strip() != ""
            and str(control).strip() not in excluded_controls
        ):
            chosen = str(control).strip()
            break

    # Falls es ursprünglich Matches gab, aber alle ausgeschlossen wurden:
    if had_match and chosen is None:
        continue

    new_row = row.copy()
    new_row["matched_control_1"] = chosen

    selected_rows.append(new_row)

# DataFrame erzeugen
result = pd.DataFrame(selected_rows)

# Alte Spalten entfernen
result = result.drop(
    columns=[
        "matched_control_1",
        "matched_control_2",
        "matched_control_3",
    ]
)

# Speichern
result.to_csv(OUTPUT_FILE, index=False)

print(f"Fertig. {len(result)} Repositories gespeichert in {OUTPUT_FILE}")