# README PLAN — AgriYield
Version: 1.0  
Date: 23 avril 2026  
Statut: Draft de cadrage (cahier des charges + spécifications)

## 1. Contexte et vision
AgriYield est une plateforme d’aide à la décision agricole basée sur une architecture microservices.  
Le système doit fournir des recommandations exploitables à partir de:
- données historiques agricoles,
- données externes temps réel (météo, marché, télédétection),
- modèles ML versionnés (baseline + fine-tuning utilisateur).

Objectif principal: aider les acteurs agricoles à anticiper les risques, comparer des scénarios et prendre des décisions rapides et justifiables.

## 2. Objectifs du projet
1. Mettre en place une architecture claire, modulaire et scalable.
2. Isoler les responsabilités de chaque service.
3. Industrialiser le cycle de vie ML (entraînement, versioning, activation, rollback).
4. Fournir une interface unifiée React pour visualisation, simulation, alertes, gouvernance modèles.
5. Garantir traçabilité, observabilité et qualité des décisions.

## 3. Périmètre (Scope)
Inclus:
- Frontend React (dashboard et gouvernance modèles).
- Backend Spring Cloud (Gateway, Config, Discovery, Decision, Integration, AgriData).
- Service ML Python (FastAPI, entraînement, prédiction, simulation, alertes, performance).
- MySQL pour la persistance métier.
- Registry d’artefacts ML (joblib + registry json).

Hors périmètre immédiat:
- MLOps avancé type Kubernetes complet.
- IAM entreprise complet (SSO/OAuth2 avancé).
- Monitoring distribué complet (OpenTelemetry full stack) en phase 1.

## 4. Cahier des charges fonctionnel
1. L’utilisateur peut charger un dataset CSV pour fine-tuning.
2. L’utilisateur visualise les métriques du modèle actif et du candidat.
3. L’utilisateur choisit explicitement le modèle à activer.
4. L’utilisateur peut revenir au modèle baseline.
5. L’utilisateur peut simuler des variations climatiques et observer l’impact en temps réel.
6. L’utilisateur reçoit des alertes et recommandations décisionnelles.
7. L’utilisateur peut consulter les performances et l’explicabilité du modèle.
8. Le système centralise la communication via API Gateway.
9. Les services backend sont configurés de manière centralisée et découverts via Eureka.

## 5. Spécifications techniques
## 5.1 Architecture
- Frontend: React + Vite + Tailwind + Plotly
- Gateway: Spring Cloud Gateway
- Service Discovery: Eureka
- Configuration centralisée: Spring Config Server
- Services métier: `agriData`, `integration`, `decision`
- ML: FastAPI + scikit-learn/XGBoost
- DB: MySQL
- Orchestration locale: `local-stack.sh`
- Contrats API: `docs/CONTRACTS.md`

## 5.2 Principes techniques
1. API-first: contrats stables et versionnables.
2. Single responsibility: chaque service possède un rôle clair.
3. Loose coupling: communication REST via Gateway et clients dédiés.
4. Resilience by design: timeouts, retries, fallback sur APIs externes.
5. ML governance: versioning des modèles, activation contrôlée, rollback baseline.
6. Observabilité: logs corrélés, métriques endpoints, suivi latence/erreurs.

## 6. Description par service
## 6.1 `configServer`
- Rôle: centraliser la configuration runtime de tous les services.
- Entrées: fichiers `config-repo`.
- Sorties: propriétés injectées aux services.
- Critères: démarrage sans config locale hardcodée.

## 6.2 `discoveryServer`
- Rôle: registre Eureka des services.
- Critères: tous les services backend enregistrés et visibles.

## 6.3 `gateway`
- Rôle: point d’entrée unique, routage, CORS.
- Critères: tous les endpoints publics passent par `:8081`.

## 6.4 `agriData`
- Rôle: gestion CRUD des données agricoles métier.
- Persistance: MySQL.
- Critères: intégrité des données et endpoints de recherche stables.

## 6.5 `integration`
- Rôle: agrégation des signaux externes temps réel.
- Entrées: APIs météo/marché/NDVI.
- Sorties: score de risque normalisé pour `decision`.
- Critères: gestion des indisponibilités externes.

## 6.6 `ml-python`
- Rôle: entraînement, fine-tuning, prédiction, simulation, alertes, performance.
- Artefacts: modèles + registry + métriques.
- Critères: activation modèle explicite, baseline non supprimable, rollback fonctionnel.

## 6.7 `decision`
- Rôle: orchestrer ML + signaux externes et produire la décision finale.
- Entrées: `ml-python` et `integration`.
- Sorties: score de risque + recommandations métier.
- Critères: réponse unifiée cohérente et traçable.

## 6.8 `frontend/react`
- Rôle: UX de pilotage.
- Modules: vue d’ensemble, simulateur, alertes, performances, gestion modèles.
- Critères: fluidité, lisibilité, mise à jour en temps réel.

## 7. Use-cases principaux
1. UC-01 — Consultation globale
Acteur: utilisateur
Résultat attendu: tableau de bord chargé avec données et métriques actives.

2. UC-02 — Simulation climatique
Acteur: utilisateur
Résultat attendu: variation des curseurs => recalcul automatique des projections.

3. UC-03 — Génération d’alertes
Acteur: utilisateur
Résultat attendu: alertes et recommandations mises à jour automatiquement.

4. UC-04 — Fine-tuning modèle
Acteur: utilisateur
Résultat attendu: upload CSV, entraînement candidat, affichage métriques comparatives.

5. UC-05 — Activation d’un modèle
Acteur: utilisateur
Résultat attendu: modèle sélectionné devient actif et tout le dashboard se recalibre.

6. UC-06 — Gouvernance des modèles
Acteur: utilisateur
Résultat attendu: renommer, supprimer (sauf baseline), revenir baseline.

7. UC-07 — Décision consolidée
Acteur: utilisateur métier
Résultat attendu: décision intégrant prédiction ML + signaux externes.

## 8. Scénarios de référence
1. Scénario nominal
Frontend -> Gateway -> Decision -> ML + Integration -> réponse consolidée -> affichage.

2. Scénario fine-tune validé
Upload CSV -> entraînement candidat -> recommandation -> activation manuelle -> production.

3. Scénario rollback
Modèle actif dégradé -> action “revenir baseline” -> système restauré.

4. Scénario API externe indisponible
Integration passe en mode fallback -> Decision continue avec signal partiel + avertissement.

5. Scénario registry corrompu
ML service applique stratégie de recovery minimale + blocage des activations invalides.

## 9. Critères de validation (acceptance)
1. Tous les services démarrent et s’enregistrent dans Eureka.
2. Tous les endpoints principaux passent via Gateway sans erreur CORS.
3. UC-01 à UC-07 exécutables de bout en bout.
4. Fine-tuning produit un candidat versionné avec métriques visibles.
5. Activation modèle met à jour immédiatement les prédictions.
6. Baseline non supprimable et rollback fonctionnel.
7. Les erreurs externes n’arrêtent pas la chaîne de décision.
8. Contrats API conformes au document `docs/CONTRACTS.md`.
9. Temps de réponse p95 acceptable en local (cible initiale < 800 ms sur endpoints métier hors entraînement).

## 10. Exigences non fonctionnelles
- Fiabilité: disponibilité locale stable des services.
- Performance: latence contrôlée sur endpoints synchrones.
- Sécurité: validation d’entrée, gestion CORS, secrets externalisés.
- Maintenabilité: séparation claire des domaines, docs et contrats à jour.
- Traçabilité: logs exploitables, version de modèle incluse dans les réponses.

## 11. Roadmap d’implémentation
Phase 1: Stabilisation architecture et contrats.
Phase 2: Intégration réelle des APIs externes + robustesse.
Phase 3: Gouvernance ML avancée + métriques d’observabilité.
Phase 4: Durcissement qualité (tests end-to-end, perf, sécurité).
Phase 5: Préparation production (CI/CD renforcée, monitoring complet).

## 12. Risques et mitigations
1. Couplage fort inter-services
Mitigation: contrats stricts, tests de contrat.

2. Données externes instables
Mitigation: cache, timeout, retry, fallback.

3. Surévaluation ML
Mitigation: protocoles d’évaluation temporelle, jeux de test séparés.

4. Dérive modèle
Mitigation: suivi métriques live + politique de rollback baseline.

5. Dette documentaire
Mitigation: update doc obligatoire à chaque changement de contrat.

## 13. Livrables attendus
1. Architecture documentée et validée.
2. Contrats API versionnés.
3. Services opérationnels localement.
4. Frontend complet avec gouvernance modèles.
5. Pipeline ML reproductible (baseline + fine-tune + activation).
6. Jeu de tests de validation fonctionnelle.

