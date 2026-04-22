# Microservice Gateway

## Description
Ce microservice agit comme un point d'entrée unique pour l'application, gérant la distribution des requêtes vers les différents microservices. Il utilise Spring Cloud Gateway avec Eureka pour la découverte de services.

## Technologies utilisées
- Spring Boot 3.4.4
- Java 21
- Spring Cloud 2024.0.1
- Spring Cloud Gateway
- Netflix Eureka
- Spring Cloud Config

## Fonctionnalités principales

### Gestion des routes
- Routage intelligent des requêtes
- Load balancing automatique
- Proxy vers les microservices
- Gestion des headers
- Transformation des requêtes/réponses

### Sécurité
- Authentification JWT
- Autorisation basée sur les rôles
- Rate limiting
- Gestion des tokens
- Blacklisting des IP

### Monitoring
- Métriques Prometheus
- Logs centralisés
- Monitoring des performances
- Tracking des erreurs
- Alerting

## Structure du projet

### Configuration
- Routes définies via application.yml
- Découverte de services via Eureka
- Configuration centralisée
- Sécurité configurée via Spring Security

### Points d'entrée API

#### Routes principales
```http
GET /api/**: Routage vers les microservices
POST /api/**: Routage vers les microservices
DELETE /api/**: Routage vers les microservices
```

#### Monitoring
```http
GET /actuator/health: Statut de la gateway
GET /actuator/metrics: Métriques de performance
GET /actuator/routes: Routes configurées
```

## Configuration requise
- Java 21
- Maven
- Service Eureka (discoveryServer)
- Service Config (configServer)
- Base de données (pour la configuration)

## Déploiement
Le microservice doit être déployé en premier, avant les autres services. Il nécessite une configuration correcte des ports et des services dépendants.

## Sécurité
- Toutes les routes sont protégées par JWT
- Validation des tokens à chaque requête
- Rate limiting configuré
- Gestion des CORS
- Protection contre les attaques CSRF

## Best Practices
- Configuration des timeouts
- Gestion des erreurs centralisée
- Logging détaillé
- Monitoring des performances
- Sécurité renforcée

## Métriques clés
- Temps de réponse moyen
- Nombre de requêtes
- Taux d'erreurs
- Utilisation des ressources
- Performance du routage

## Logging et Monitoring
- Logs centralisés
- Métriques Prometheus
- Monitoring des performances
- Alerting sur les erreurs
- Tracking des performances

## Maintenance
- Mise à jour des routes
- Optimisation du routage
- Monitoring des performances
- Tests d'intégration
- Sauvegarde de la configuration

## Support
Pour toute question ou problème, contacter l'équipe de support.