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

## 14. Zones à implémenter (plan d’exécution par service)
Objectif: passer d’un prototype fonctionnel à une plateforme vendable, robuste et compréhensible pour les acteurs métier.

### 14.1 Priorités globales
- P0 (bloquant vente): sécurité, traçabilité, qualité des données, résilience décisionnelle.
- P1 (forte valeur): notifications, reporting, batch décisionnel, gouvernance avancée.
- P2 (scale): facturation, multi-région, MLOps avancé.

### 14.2 Backlog par service existant
| Service | Zone à implémenter | Priorité | Détails d’implémentation | Definition of Done |
|---|---|---|---|---|
| `gateway` | AuthN/AuthZ centralisée + propagation identité | P0 | Validation JWT, contrôle des rôles, propagation `X-User-Id` / `X-Tenant-Id`, rejet des requêtes non authentifiées | Endpoints protégés, tests d’accès par rôle, logs d’audit d’accès |
| `gateway` | Rate limiting et protection API | P0 | Limite par clé API/tenant, anti-abus, quotas par plan | Limites configurables par tenant, métriques de rejet visibles |
| `gateway` | Correlation IDs et standard d’erreur | P0 | Injection systématique `X-Correlation-Id`, format d’erreur unifié (`code`, `message`, `details`) | Tous les services renvoient un format homogène via Gateway |
| `gateway` | Résilience de routage | P1 | Timeout, retry, circuit breaker sur routes critiques | Pannes d’un service ne bloquent pas toute la plateforme |
| `configServer` | Templates de config par environnement | P0 | Structurer `dev/staging/prod`, secrets externalisés, valeurs par défaut sûres | Démarrage identique entre environnements, sans secret en dur |
| `discoveryServer` | Durcissement prod | P1 | Health checks, tuning TTL/heartbeat, dashboard d’état | Tous les services détectés, alertes en cas de perte d’instance |
| `agriData` | CRUD complet + versioning dataset | P0 | Ajouter update/delete/version dataset, provenance, hash dataset | Traçabilité complète de la donnée source à la décision |
| `agriData` | Validation et qualité des données | P0 | Schéma strict, règles métier (bornes année/pluie/temp), rejet explicite des lignes invalides | Rapport de qualité disponible avant ingestion |
| `agriData` | API de couverture temporelle | P0 | Endpoint `coverage` par pays/culture (`year_min`, `year_max`, `rows`) | Frontend et décision utilisent la même vérité temporelle |
| `integration` | Remplacer le stub par adaptateurs réels | P0 | Connecteurs météo/marché/NDVI, mapping vers schéma canonique, fallback local | Signaux en production proviennent de vraies sources externes |
| `integration` | Cache et gestion indisponibilités | P0 | Cache TTL, fallback sur dernière valeur valide, score de fraîcheur | Décision continue même en cas de panne fournisseur |
| `integration` | Historisation des signaux | P1 | Stocker signaux et latences fournisseurs, rejouer l’historique | Audit possible des décisions passées |
| `decision` | Moteur de règles configurable | P0 | Externaliser les poids/thresholds (pas hardcodés), versionner les policies | Ajustement métier sans recompilation |
| `decision` | Explicabilité de la décision | P0 | Retourner contribution par facteur (`ml`, `weather`, `market`, `ndvi`) + niveau de confiance | Réponse exploitable par décideur non technique |
| `decision` | Mode batch et priorisation | P1 | Endpoint d’analyse multi-zones, classement par criticité | Génération de listes d’actions régionales |
| `ml-python` | Évaluation temporelle (anti fuite) | P0 | Séparer entraînement/validation par temps, pas seulement split aléatoire | Métriques robustes et crédibles en contexte réel |
| `ml-python` | Contrat de couverture modèle | P0 | Inclure `year_min/year_max`, `dataset_hash`, `dataset_source` dans état/registry | Gouvernance claire des limites temporelles du modèle |
| `ml-python` | Promotion contrôlée des candidats | P1 | Politique explicite: auto-promote, approval manuelle, rollback policy | Comportement de promotion prédictible et documenté |
| `ml-python` | Détection de drift | P1 | Drift data/performance, alertes de recalibration | Alerte précoce avant dégradation opérationnelle |
| `frontend/react` | Espace “Confiance décision” | P0 | Afficher source des signaux, fraîcheur, version modèle, limites temporelles | Décisions justifiées et compréhensibles |
| `frontend/react` | Gestion des rôles et tenants | P0 | Vues conditionnées par rôle (admin/analyste/lecteur), périmètre tenant | Isolation fonctionnelle par organisation |
| `frontend/react` | Export opérationnel | P1 | Export PDF/CSV des décisions, scénarios et alertes | Partage facile avec coopératives et autorités |
| `frontend/react` | Gestion d’erreurs UX | P1 | Etats dégradés clairs (données partielles, source externe indisponible) | UX stable et non bloquante en incident |

## 15. Services additionnels recommandés (pour un produit vendable)
Ces services sont recommandés pour obtenir une offre réellement commercialisable.

### 15.1 `identity-access-service` (P0)
Rôle:
- Authentification, gestion utilisateurs, rôles, tenants.
- Émission et rotation des tokens.

Contrats minimaux:
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /users/me`
- `GET /tenants/{id}/members`
- `POST /roles/assign`

Pourquoi indispensable:
- Sans IAM multi-tenant, le produit reste un démonstrateur technique.

### 15.2 `audit-log-service` (P0)
Rôle:
- Journal append-only de toutes les actions critiques (activation modèle, upload dataset, décision générée).

Contrats minimaux:
- `POST /audit/events`
- `GET /audit/events?tenantId=&from=&to=&type=`

Pourquoi indispensable:
- Confiance, conformité, relecture métier des décisions.

### 15.3 `notification-service` (P1)
Rôle:
- Diffusion des alertes (email/SMS/WhatsApp/push) selon sévérité et zone.

Contrats minimaux:
- `POST /notifications/send`
- `POST /notifications/rules`
- `GET /notifications/history`

Pourquoi indispensable:
- La valeur métier repose sur l’action rapide, pas seulement l’affichage dashboard.

### 15.4 `reporting-service` (P1)
Rôle:
- Génération de rapports périodiques (PDF/CSV) par culture, zone et période.

Contrats minimaux:
- `POST /reports/generate`
- `GET /reports/{reportId}`

Pourquoi utile:
- Facilite la vente B2B institutionnelle (coopératives, ministères, ONG, agro-industrie).

### 15.5 `billing-subscription-service` (P2)
Rôle:
- Plans, quotas, facturation, suivi consommation API.

Pourquoi utile:
- Nécessaire pour l’industrialisation commerciale, mais pas bloquant en phase pilote.

## 16. Contrats transverses à standardiser (obligatoires)
1. Tous les services doivent accepter et propager:
- `X-Correlation-Id`
- `X-Tenant-Id`
- `X-User-Id`

2. Toutes les réponses métier doivent exposer:
- `timestamp`
- `model_version` (si décision liée au ML)
- `data_coverage` (`year_min`, `year_max`)
- `signal_freshness` (si données externes)

3. Standard d’erreur unique:
```json
{
  "code": "INTEGRATION_TIMEOUT",
  "message": "Le fournisseur météo ne répond pas",
  "details": {},
  "correlationId": "..."
}
```

## 17. Plan d’implémentation recommandé (12 semaines)
### Sprint 1-2 (P0 architecture fiable)
- Standard d’erreur + correlation IDs.
- Couverture temporelle dataset/modèle exposée partout.
- Validation stricte des données dans `agriData`.

### Sprint 3-4 (P0 sécurité et traçabilité)
- `identity-access-service` + protection Gateway.
- `audit-log-service` + événements critiques.

### Sprint 5-6 (P0 décision robuste)
- `integration` réel (au moins 1 fournisseur par signal) + fallback/cache.
- `decision` explicable (contributions + confiance).

### Sprint 7-8 (P1 valeur opérationnelle)
- `notification-service`.
- Export reporting.
- Batch d’analyse multi-zones.

### Sprint 9-10 (P1 qualité ML)
- Validation temporelle ML + règles de promotion explicites.
- Alertes de drift.

### Sprint 11-12 (Go-to-market)
- Durcissement performance/sécurité.
- Test E2E multi-tenant.
- Dossier de démo client (cas d’usage + KPIs + SLA).

## 18. Critères “projet vendable” (Go/No-Go)
Go si tous les points suivants sont vrais:
1. Multi-tenant sécurisé en production pilote.
2. Décisions traçables de bout en bout (qui, quand, avec quel modèle et quelles données).
3. Sources externes réelles avec mécanisme de continuité de service.
4. Alertes diffusables hors interface web (notification active).
5. Rapport exploitable par décideur non technique.
6. Taux de disponibilité et latence observés sur une période pilote documentée.

## 19. Décision d’architecture recommandée
Pour rester “propre et claire”:
1. Conserver les services actuels (socle valide).
2. Ajouter d’abord 3 services: `identity-access`, `audit-log`, `notification`.
3. Implémenter `reporting` ensuite.
4. Reporter `billing` après validation terrain.

Cette trajectoire minimise la complexité initiale tout en maximisant la valeur commerciale et la confiance des acteurs concernés.
