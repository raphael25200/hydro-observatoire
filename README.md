# Débits des rivières — Observatoire

Un outil en ligne de commande et un tableau de bord interactif pour suivre l'évolution du débit des rivières françaises, à partir des données publiques [Hub'Eau](https://hubeau.eaufrance.fr/).

Projet né pendant la canicule de juillet 2026, en observant l'assèchement de l'Allan à Montbéliard — et l'occasion de construire une première vraie pratique autonome de Python (data/pandas), après une reconversion PHP/Symfony → data.

![Aperçu du dashboard](docs/screenshot-dashboard.png)

## Ce que ça fait

**`analyse.py`** — un analyseur CLI qui :

- charge deux relevés journaliers (début / fin de période)
- nettoie les données (débits négatifs, révisions dupliquées)
- calcule la variation de débit par station entre les deux dates
- affiche un rapport (stats descriptives, top 10 des plus fortes baisses)
- exporte les données pour le dashboard

**`dashboard.html`** — un tableau de bord interactif (HTML/JS autonome, sans serveur) qui :

- affiche une carte de France colorée selon la variation de débit (dégradé + forme distincte pour l'accessibilité)
- interroge l'API Hub'Eau en direct pour une période choisie dynamiquement
- permet de sélectionner des stations (sur la carte ou dans un tableau triable/filtrable) et de comparer leur historique sur un graphique
- exporte les données sélectionnées en CSV
- renvoie vers les fiches officielles (Vigicrues, HydroPortail) pour chaque station

## Aperçu

![Détail d'une station sur la carte](docs/screenshot-dashboard-2.png)
_Carte interactive avec dégradé de couleur selon la variation de débit_

![Comparaison de plusieurs stations](docs/screenshot-dashboard-3.png)
_Graphique d'historique, plusieurs stations superposées_

![Tableau et sélection de stations](docs/screenshot-dashboard-4.png)
_Tableau triable/filtrable, sélection synchronisée avec la carte_

## Installation

Prérequis : Python 3.10+

```bash
git clone <url-du-repo>
cd csv-analyzer
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows PowerShell
pip install pandas
```

## Utilisation

### 1. Récupérer des données (API Hub'Eau)

```powershell
Invoke-WebRequest -Uri "https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab.csv?grandeur_hydro_elab=QmnJ&date_debut_obs_elab=2026-07-08&date_fin_obs_elab=2026-07-08&size=6000" -OutFile "jour_debut.csv"
Invoke-WebRequest -Uri "https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab.csv?grandeur_hydro_elab=QmnJ&date_debut_obs_elab=2026-07-16&date_fin_obs_elab=2026-07-16&size=6000" -OutFile "jour_fin.csv"
```

(Le référentiel des stations, `toutes_stations.csv`, est déjà inclus dans le repo — pas besoin de le retélécharger sauf si tu veux des données à jour.)

### 2. Lancer l'analyse

```powershell
python analyse.py jour_debut.csv jour_fin.csv --date-debut 2026-07-08 --date-fin 2026-07-16
```

### 3. Ouvrir le dashboard

Double-clique sur `dashboard.html` — il fonctionne directement dans le navigateur, sans serveur, et interroge l'API Hub'Eau en direct pour la période de ton choix.

## Stack technique

- **Python** / **pandas** — nettoyage, jointures, agrégation
- **JavaScript vanilla** / **Leaflet** (carte) / **Chart.js** (graphiques) — pas de framework, pas de build, un seul fichier HTML autonome
- **API Hub'Eau** (Ministère de la Transition écologique) — source des données

## Méthodologie et limites

- Le "% de variation" affiché est un **indicateur exploratoire maison**, calculé sur la période choisie. Il ne correspond **pas** aux seuils réglementaires officiels de sécheresse (DSA/DAR/DCR), qui reposent sur des débits seuils absolus propres à chaque station, définis par arrêté préfectoral. Pour un suivi officiel : [VigiEau](https://vigieau.gouv.fr).
- Les mesures avec une qualification "douteuse" ou "incertaine" côté Hub'Eau sont exclues du calcul.
- Les données très récentes (< 3 jours environ) sont souvent encore en cours de validation côté Hub'Eau et peuvent être incomplètes.

## Quelques problèmes réels rencontrés (et corrigés)

Pour la transparence — et parce que ça fait partie de l'apprentissage :

- **Doublons de révision** : Hub'Eau republie parfois une mesure corrigée sous une nouvelle ligne (même jour, `date_prod` différent). Sans déduplication, un `merge()` naïf peut produire des jointures explosives (des millions de lignes au lieu de quelques milliers).
- **Mauvais nom de paramètre d'API** : `code_station` semble être le nom logique pour filtrer une station sur l'endpoint `obs_elab`, mais Hub'Eau attend en réalité `code_entite`. Sans ce paramètre correct, l'API ignore silencieusement le filtre et renvoie les données nationales non filtrées — aucune erreur explicite, juste des résultats incohérents à déboguer.
- **Valeurs aberrantes non signalées** : certaines mesures brutes contiennent des valeurs physiquement impossibles (débits négatifs, pics ×1000), sans toujours être marquées comme telles par l'API.

## Licence des données

Données Hub'Eau sous [licence ouverte Etalab 2.0](https://github.com/etalab/licence-ouverte/blob/master/LO.md).

## Auteur

Raphaël Navarro — [LinkedIn](https://www.linkedin.com/in/navarroraphael/) · [Malt](https://www.malt.fr/profile/raphaelnavarro)
