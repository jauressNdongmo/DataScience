# Microservice Discovery Server (Eureka)

## Description
Ce microservice agit comme un serveur de découverte de services pour l'application. Il utilise Netflix Eureka pour gérer la découverte et le registre des microservices.

## Technologies utilisées
- Spring Boot 3.4.4
- Java 21
- Spring Cloud 2024.0.1
- Netflix Eureka Server
- Prometheus pour la métrique

## Fonctionnalités principales

### Gestion des services
- Registre des microservices
- Découverte automatique des services
- Health check des services
- Interface de monitoring
- Gestion des instances

### Monitoring
- Dashboard Eureka
- Métriques Prometheus
- Logs centralisés
- Tracking des services
- Alerting

## Structure du projet

### Configuration
- Application.yml pour le port et la configuration Eureka
- Sécurité configurée via Spring Security
- Métriques configurées
- Configuration du dashboard

### Points d'entrée API

#### Gestion des services
```http
GET /eureka/apps: Liste des services enregistrés
GET /eureka/apps/{app-name}: Détails d'un service
GET /eureka/v2/apps: Liste des applications
```

#### Monitoring
```http
GET /actuator/health: Statut du serveur
GET /actuator/metrics: Métriques de performance
GET /eureka/dashboard: Dashboard Eureka
```

## Configuration requise
- Java 21
- Maven
- Port 8761 (par défaut)
- Base de données (pour la configuration)

## Déploiement
Le microservice doit être déployé en premier, avant les autres services. Il nécessite une configuration correcte des ports et des services dépendants.

## Sécurité
- Authentification basique
- Sécurité du dashboard
- Protection des endpoints
- Rate limiting
- Gestion des CORS

## Best Practices
- Configuration des timeouts
- Gestion des erreurs centralisée
- Logging détaillé
- Monitoring des performances
- Sécurité renforcée

## Métriques clés
- Nombre de services enregistrés
- Temps de réponse
- Taux de réussite des requêtes
- Utilisation des ressources
- Performance du registre

## Logging et Monitoring
- Logs centralisés
- Métriques Prometheus
- Monitoring des performances
- Alerting sur les erreurs
- Tracking des services

## Maintenance
- Mise à jour des configurations
- Optimisation du registre
- Monitoring des performances
- Tests d'intégration
- Sauvegarde des configurations

## Support
Pour toute question ou problème, contacter l'équipe de support.