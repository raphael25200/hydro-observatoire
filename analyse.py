"""
Analyseur de débits des rivières françaises (données Hub'Eau).

Compare le débit de chaque station hydrométrique entre deux dates, calcule
la variation en %, affiche un rapport en console et exporte les données
pour le dashboard interactif (dashboard.html).

Utilisation :
    python analyse.py fichier_debut.csv fichier_fin.csv
    python analyse.py fichier_debut.csv fichier_fin.csv --date-debut AAAA-MM-JJ --date-fin AAAA-MM-JJ

Exemple :
    python analyse.py jour_debut.csv jour_fin.csv --date-debut 2026-07-08 --date-fin 2026-07-16

Les deux fichiers CSV s'obtiennent via l'API Hub'Eau, par exemple :
    Invoke-WebRequest -Uri "https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab.csv?grandeur_hydro_elab=QmnJ&date_debut_obs_elab=AAAA-MM-JJ&date_fin_obs_elab=AAAA-MM-JJ&size=6000" -OutFile "jour_debut.csv"

Nécessite aussi "toutes_stations.csv" dans le même dossier (référentiel des
stations, nom de rivière/commune/coordonnées) — voir le README pour l'obtenir.

--date-debut / --date-fin sont optionnels : ils ne servent qu'à l'affichage
(la comparaison se base sur les dates réellement présentes dans les fichiers).
"""

import pandas as pd
import argparse

# --- Récupération des arguments ---
# Deux fichiers requis : l'état au début et à la fin de la période à comparer
parser = argparse.ArgumentParser()
parser.add_argument("fichier_debut", help="CSV du premier jour")
parser.add_argument("fichier_fin", help="CSV du dernier jour")
parser.add_argument("--date-debut", default="?", help="Date du fichier de début")
parser.add_argument("--date-fin", default="?", help="Date du fichier de fin")
args = parser.parse_args()

print(f"Période analysée : {args.date_debut} → {args.date_fin}")
print()

# --- Chargement des deux fichiers ---
df_debut = pd.read_csv(args.fichier_debut, sep=";")
df_fin = pd.read_csv(args.fichier_fin, sep=";")

# Certaines mesures sont révisées plusieurs fois pour un même jour (correction a posteriori) :
# on ne garde que la révision la plus récente par station (date_prod le plus grand).
df_debut = df_debut.sort_values("date_prod", ascending=False).drop_duplicates(subset="code_station")
df_fin = df_fin.sort_values("date_prod", ascending=False).drop_duplicates(subset="code_station")

# --- Nettoyage : on enlève les débits négatifs (valeurs aberrantes) ---
print(f"{(df_debut['resultat_obs_elab'] < 0).sum()} lignes négatives supprimées (début)")
df_debut = df_debut[df_debut["resultat_obs_elab"] >= 0]
print(f"{(df_fin['resultat_obs_elab'] < 0).sum()} lignes négatives supprimées (fin)")
df_fin = df_fin[df_fin["resultat_obs_elab"] >= 0]

# --- Mesures douteuses, incertaines ou mauvaises : exclues (comme dans dashboard.html) ---
QUALIF_EXCLUES = "douteuse|incertaine|mauvaise"
q_debut = df_debut["libelle_qualification"].fillna("").str.contains(QUALIF_EXCLUES, case=False)
print(f"{q_debut.sum()} mesures douteuses/incertaines exclues (début)")
df_debut = df_debut[~q_debut]
q_fin = df_fin["libelle_qualification"].fillna("").str.contains(QUALIF_EXCLUES, case=False)
print(f"{q_fin.sum()} mesures douteuses/incertaines exclues (fin)")
df_fin = df_fin[~q_fin]

# --- Résumé rapide sur le fichier de fin ---
print()
print("=== Aperçu (fichier fin) ===")
print(df_fin.head())
print()
print("=== Dimensions ===")
print(f"Début : {df_debut.shape[0]} lignes — Fin : {df_fin.shape[0]} lignes")
print()
print("=== Statistiques descriptives (fin) ===")
print(df_fin["resultat_obs_elab"].describe())
print()

# --- Jointure des deux fichiers sur code_station ---
resultats = df_debut.merge(df_fin, on="code_station", suffixes=("_debut", "_fin"))
resultats = resultats[["code_station", "resultat_obs_elab_debut", "resultat_obs_elab_fin"]]
resultats = resultats.rename(columns={
    "resultat_obs_elab_debut": "first",
    "resultat_obs_elab_fin": "last"
})
print(f"{len(resultats)} stations présentes dans les deux fichiers")
print()

# --- Calcul de la variation en % ---
resultats["variation_pct"] = (resultats["last"] - resultats["first"]) / resultats["first"] * 100

# On exclut les cas où la division par zéro donne NaN ou inf (station à sec au départ)
resultats_valides = resultats[
    resultats["variation_pct"].notna() & (resultats["variation_pct"] != float("inf"))
]
print(f"{len(resultats_valides)} stations avec une variation calculable")
print()
print("Note : le % de variation est un indicateur exploratoire (calculé sur la période donnée),")
print("il ne correspond pas aux seuils réglementaires officiels de sécheresse (DSA/DAR/DCR, VigiEau).")
print()

# --- Référentiel des stations (nom de rivière, commune, coordonnées) ---
# Une seule lecture, réutilisée à la fois pour l'affichage du top 10 et l'export du dashboard.
df_ref = pd.read_csv("toutes_stations.csv", sep=";")
df_ref = df_ref[["code_station", "libelle_cours_eau", "libelle_commune", "latitude_station", "longitude_station"]]
df_ref = df_ref.dropna(subset=["latitude_station", "longitude_station"])

# Stations calculables mais absentes du référentiel : elles n'apparaîtront pas dans le top 10
n_hors_ref = (~resultats_valides["code_station"].isin(df_ref["code_station"])).sum()
print(f"{n_hors_ref} stations calculables absentes du référentiel (sans nom de cours d'eau)")
print()

# --- Top 10 des plus fortes baisses, enrichi avec le nom de la rivière ---
print("=== Top baisses ===")
top_baisses = resultats_valides.sort_values("variation_pct").head(10)
top_baisses = top_baisses.merge(
    df_ref[["code_station", "libelle_cours_eau", "libelle_commune"]], on="code_station"
)
print(top_baisses[["code_station", "libelle_cours_eau", "libelle_commune", "first", "last", "variation_pct"]])
print()

# --- Export pour le dashboard interactif (dashboard.html) ---
json_str = df_ref.to_json(orient="records", force_ascii=False)
with open("stations_ref.js", "w", encoding="utf-8") as f:
    f.write(f"const STATIONS_REF = {json_str};")
print("stations_ref.js généré (utilisé par dashboard.html)")