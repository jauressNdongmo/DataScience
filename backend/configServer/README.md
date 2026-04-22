# Microservice Config Server

## Description
Ce microservice gère la configuration centralisée de tous les microservices de l'application. Il utilise Spring Cloud Config avec Git pour stocker et distribuer les configurations.

## Technologies utilisées
- Spring Boot 3.4.4
- Java 21
- Spring Cloud 2024.0.1
- Spring Cloud Config Server
- Git pour le stockage des configurations
- Netflix Eureka Client
- Prometheus pour la métrique

## Fonctionnalités principales

### Gestion des configurations
- Stockage centralisé des configurations
- Versioning des configurations
- Distribution des configurations
- Support des profils (dev, prod, etc.)
- Gestion des propriétés

### Synchronisation
- Synchronisation avec Git
- Support des branches
- Gestion des commits
- Détection des changements
- Rollback des configurations

### Monitoring
- Métriques Prometheus
- Logs centralisés
- Tracking des changements
- Alerting
- Statistiques d'utilisation

## Structure du projet

### Configuration
- Application.yml pour le port et la configuration
- Configuration Git
- Profils de configuration
- Sécurité configurée
- Métriques configurées

### Points d'entrée API

#### Gestion des configurations
```http
GET /{application}/{profile}/{label}: Récupération des configurations
GET /{application}/{profile}: Récupération des configurations (latest)
GET /{application}/{profile}/{label}/{path}: Récupération d'un fichier
```

#### Monitoring
```http
GET /actuator/health: Statut du serveur
GET /actuator/metrics: Métriques de performance
GET /actuator/env: Environnement de configuration
```

## Configuration requise
- Java 21
- Maven
- Git (pour le stockage des configurations)
- Repository Git configuré
- Port 8888 (par défaut)
- Service Eureka (pour la découverte)

## Déploiement
Le microservice doit être déployé en premier, avant les autres services. Il nécessite une configuration correcte des ports et des services dépendants.

## Sécurité
- Authentification basique
- Sécurité des endpoints
- Protection des configurations
- Rate limiting
- Gestion des CORS

## Best Practices
- Organisation des configurations par microservice
- Utilisation des profils
- Documentation des configurations
- Tests de configuration
- Sauvegarde des configurations

## Métriques clés
- Nombre de configurations
- Temps de réponse
- Taux de réussite des requêtes
- Utilisation des ressources
- Performance du serveur

## Logging et Monitoring
- Logs centralisés
- Métriques Prometheus
- Monitoring des performances
- Alerting sur les erreurs
- Tracking des changements

## Maintenance
- Mise à jour des configurations
- Optimisation du stockage
- Monitoring des performances
- Tests d'intégration
- Sauvegarde des configurations

## Support
Pour toute question ou problème, contacter l'équipe de support.