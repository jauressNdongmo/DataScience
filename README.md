# Agri Decision Platform (Microservices)

Plateforme de data science agricole pour la prévision de rendement, l'analyse de risque et l'aide à la décision opérationnelle.

## Stack technique

- Backend: Spring Boot + Spring Cloud
- Frontend: React + Vite + Tailwind + Plotly
- ML: Python FastAPI (service dédié)
- Base de données: MySQL
- Découverte/config: Eureka + Config Server
- Orchestration: Docker Compose (ou script local)

## Architecture système

### Vue logique

```text
[Frontend React]
      |
      v
[Gateway]
  |      \
  |       \----> [Decision Service] ----> [Integration Service]
  |                         |                     |
  |                         |                     +--> (APIs externes météo/marché/satellite)
  |                         |
  |                         +----> [ML Python Service]
  |
  +----> [Agri Data Service] ----> [MySQL]

[Config Server] -> centralise les propriétés de tous les services
[Discovery Server] -> registre des services (Eureka)
```

### Flux principal de décision

1. Le frontend envoie la demande via le Gateway.
2. `decision` orchestre:
   - appel à `ml-python` pour la prédiction,
   - appel à `integration` pour les signaux externes (weather risk, market index, NDVI).
3. `decision` calcule le niveau de risque et renvoie recommandations + score agrégé.

## Services (explication claire)

### 1) `discoveryServer`
- Rôle: registre de services (Eureka).
- Utilité: permet à Gateway et aux microservices de se découvrir dynamiquement.
- Port: `8090`.

### 2) `configServer`
- Rôle: serveur de configuration centralisée.
- Source de config: dossier local `config-repo/` (pas de dépendance à un repo Git distant).
- Utilité: un seul point de vérité pour les propriétés `dev`/`docker`.
- Port: `8888`.

### 3) `gateway`
- Rôle: point d'entrée unique API.
- Responsabilités:
  - routage des requêtes vers les services métier,
  - CORS,
  - abstraction des URLs internes.
- Port: `8081`.

### 4) `agriData`
- Rôle: gestion des données agricoles historiques.
- Persistance: MySQL (`agri_data_db`).
- Endpoints clés:
  - `GET /records`
  - `GET /records/search?country=...&crop=...`
  - `POST /records/bulk`
- Utilité: source métier des observations terrain (pays, culture, pluie, température, intrants, rendement).

### 5) `integration`
- Rôle: contrat unifié avec les données externes temps réel.
- Endpoints clés:
  - `GET /signals/realtime?country=...&crop=...`
- État actuel: implémentation `stub` déterministe.
- Cible: brancher vraies APIs météo, prix marché, télédétection (NDVI).

### 6) `ml-python`
- Rôle: entraînement, simulation, explicabilité et prédiction.
- Endpoints clés:
  - `POST /train`, `POST /train/upload`
  - `GET /overview`
  - `GET /scenario/context`, `POST /scenario/simulate`
  - `POST /alerts`
  - `GET /performance`
  - `POST /predict`
- Utilité: reproduit le flow data-science complet (équivalent interface Streamlit).

### 7) `decision`
- Rôle: orchestration métier de haut niveau.
- Endpoint clé:
  - `POST /analysis`
- Utilité: fusionne prédiction ML + signaux externes pour fournir une décision opérationnelle unifiée.

### 8) `frontend/react`
- Rôle: interface utilisateur décisionnelle.
- Fonctionnalités:
  - upload dataset,
  - onglets `Vue d'ensemble`, `Simulateur`, `Alertes & Décisions`, `Performances Modèles`,
  - graphiques Plotly,
  - métriques et panneaux de recommandations.

## Métriques, observabilité et sauvegarde des modèles (cible V2)

### A) Observabilité technique (services)

Objectif: monitorer disponibilité, latence, erreurs, capacité.

- Spring services:
  - Actuator + Micrometer + `prometheus` endpoint.
- ML Python:
  - instrumentation Prometheus (`prometheus_client`) pour latence train/predict, erreurs, modèle actif.
- Stack monitoring:
  - Prometheus (scraping)
  - Grafana (dashboards)
  - Loki/ELK (logs centralisés)
  - OpenTelemetry + Tempo/Jaeger (traces distribuées)

Métriques minimales à suivre:
- `request_count`, `error_rate`, `p95_latency` par service/endpoint
- temps d'entraînement, temps de prédiction
- taille dataset chargé
- disponibilité des APIs externes (timeouts, retries, circuit breaker ouvert)

### B) Sauvegarde et versioning des modèles

Objectif: reproductibilité, rollback, auditabilité.

- Artefacts modèle:
  - sérialiser (joblib/pickle) dans stockage objet (MinIO/S3) ou volume dédié.
- Registry modèle:
  - table MySQL ou MLflow Model Registry pour stocker:
    - `model_version`
    - date d'entraînement
    - features utilisées
    - métriques de validation (MAE/RMSE/R2)
    - hash dataset / provenance
    - statut (`staging`, `production`, `archived`)
- Chargement runtime:
  - `ml-python` charge explicitement la version `production` au startup.
- Audit:
  - journaliser `model_version` dans chaque réponse de prédiction.

### C) Données de métriques métier

Objectif: pilotage décisionnel.

Exemples:
- rendement prévu vs rendement observé (erreur réelle)
- fréquence des alertes par zone/culture
- taux de recommandations suivies
- impact économique estimé par scénario

## Lancer la plateforme

### Option Docker

```bash
./deploy-docker.sh
```

### Option locale (sans Docker)

```bash
./local-stack.sh start
```

Commandes utiles:

```bash
./local-stack.sh status
./local-stack.sh logs
./local-stack.sh stop
```

Notes:
- Le script démarre tous les services (Spring, ML Python, frontend React) en profil `dev`.
- Logs: `.local-runtime/logs/`
- PID: `.local-runtime/pids/`
- MySQL attendu: `localhost:3307` avec `springboot/springboot`.

## Configuration centralisée locale

- Dossier des configs Spring Cloud: `config-repo/`
- Monté dans `config-server` sur `/config-repo` (Docker)
- Profils pris en charge: `*-dev.properties` et `*-docker.properties`

## MySQL

- Utilisateur applicatif: `springboot`
- Mot de passe applicatif: `springboot`
- Mot de passe `root`: `mysqlServer$`
- Bases initialisées: `agri_data_db`, `integration_db`, `decision_db`

Si un volume MySQL existe déjà et que vous voulez rejouer l'init SQL:

```bash
cd deployment
docker compose down -v
```

## Endpoints principaux

- Frontend React (docker): `http://localhost:8010`
- Frontend React (local script): `http://localhost:5173`
- API Gateway: `http://localhost:8081`
- ML service (direct): `http://localhost:8000`
- phpMyAdmin: `http://localhost:8001`

## Contrats API

- Voir: `docs/CONTRACTS.md`

## Cycle de vie du modele (implemente)

Le service `ml-python` gere maintenant un cycle continu de modele:

1. **Modele baseline**
   - Entrainement initial sur le dataset de reference.
   - Sauvegarde de l'artefact + metriques dans `backend/ml-python/artifacts/`.

2. **Fine-tune utilisateur + choix explicite**
   - Quand un utilisateur charge un CSV (`POST /train/upload`), le service peut faire un `mode=finetune`.
   - Le dataset utilisateur est fusionne au dataset actif (sauf `replace_dataset=true`).
   - Le frontend affiche les resultats du candidat (R2, version) et recommande le meilleur modele.
   - L'utilisateur choisit ensuite le modele a activer.

3. **Selection manuelle du modele**
   - Le registry conserve toutes les versions (`baseline` et `finetune`).
   - On peut activer n'importe quelle version en production.

4. **Rollback vers baseline**
   - Le modele baseline est memorise dans le registry.
   - On peut revenir explicitement au baseline via endpoint dedie.

### Endpoints ML utiles (V2)

- `GET /state`: etat + version active
- `GET /model/registry`: historique + version baseline + recommandation globale
- `POST /train`: entrainement avec options (`baseline`/`finetune`)
- `POST /train/upload`: upload CSV (souvent en `promote_if_better=false` pour laisser le choix utilisateur)
- `POST /model/activate`: active une version specifique
- `POST /model/revert-baseline`: revient au modele baseline

Exemple upload fine-tune sans promotion auto:

```bash
curl -X POST "http://localhost:8081/api/ml/train/upload?mode=finetune&promote_if_better=false&replace_dataset=false" \
  -F "file=@yield_df.csv"
```

## Donnees recentes (jusqu'a 2025)

Voir le document detaille:
- `docs/DATA_SOURCES_2025.md`

Ce document liste les sources officielles pour:
- production/rendement (FAOSTAT),
- meteo/pluie/temperature (NASA POWER, NOAA CDO, CHIRPS),
- prix marche (World Bank Pink Sheet, FAO FPI),
- vegetation/NDVI (MODIS, eVIIRS).

## Bootstrap dataset baseline (officiel)

Pour reconstruire le dataset de base du modele ML (sources FAOSTAT + World Bank) :

```bash
source backend/ml-python/.venv/bin/activate
python backend/ml-python/scripts/bootstrap_base_dataset.py --min-year 1990
```

Sorties generees :
- `backend/ml-python/data/yield_df.csv` (dataset final pour entrainement)
- `backend/ml-python/data/metadata.json` (provenance + couverture)
- `backend/ml-python/data/raw/` (archives telechargees)


## Activer le modele baseline sans lancer l'application

Cette commande entraine et promeut le baseline directement depuis le terminal :

```bash
source backend/ml-python/.venv/bin/activate
python backend/ml-python/scripts/promote_baseline_model.py \
  --csv backend/ml-python/data/yield_df.csv \
  --source bootstrap-baseline-cli
```
